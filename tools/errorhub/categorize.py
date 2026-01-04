from __future__ import annotations

import csv
import datetime as dt
import glob
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Defaults:
    category: str
    severity: str
    retryable: str | bool


@dataclass(frozen=True)
class RegistryRule:
    pattern: re.Pattern[str]
    category: str
    severity: str
    retryable: str | bool


@dataclass(frozen=True)
class TextRule:
    rule_id: str
    pattern: re.Pattern[str]
    category: str
    severity: str
    retryable: str | bool


@dataclass
class RawEvent:
    raw: str
    message: str
    service: str | None = None
    level: str | None = None
    timestamp: str | None = None
    error_code: str | None = None
    extra: dict[str, Any] | None = None


@dataclass
class CategorizedEvent(RawEvent):
    category: str = "UNKNOWN"
    severity: str = "P2"
    retryable: str | bool = "unknown"
    matched_by: str = "default"
    rule_id: str | None = None


ERROR_CODE_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,9}-[A-Z0-9]{2,12}-\d{4}\b")
LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b", re.IGNORECASE)
SERVICE_KV_RE = re.compile(r"\b(?:service|svc|app)=([a-zA-Z0-9_.-]+)\b")
CODE_KV_RE = re.compile(r"\b(?:error_code|err_code|code)=([A-Z][A-Z0-9]{2,9}-[A-Z0-9]{2,12}-\d{4})\b")
ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")


def _load_config(path: Path) -> tuple[Defaults, list[RegistryRule], list[TextRule]]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    defaults_raw = cfg.get("defaults") or {}
    defaults = Defaults(
        category=str(defaults_raw.get("category", "UNKNOWN")),
        severity=str(defaults_raw.get("severity", "P2")),
        retryable=defaults_raw.get("retryable", "unknown"),
    )

    registry: list[RegistryRule] = []
    for item in (cfg.get("error_code_registry") or []):
        registry.append(
            RegistryRule(
                pattern=re.compile(str(item["pattern"])),
                category=str(item["category"]),
                severity=str(item["severity"]),
                retryable=item.get("retryable", defaults.retryable),
            )
        )

    rules: list[TextRule] = []
    for item in (cfg.get("rules") or []):
        rules.append(
            TextRule(
                rule_id=str(item["id"]),
                pattern=re.compile(str(item["regex"]), re.IGNORECASE),
                category=str(item["category"]),
                severity=str(item["severity"]),
                retryable=item.get("retryable", defaults.retryable),
            )
        )

    return defaults, registry, rules


def _iter_input_files(inputs: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for inp in inputs:
        p = Path(inp)
        has_glob = any(ch in inp for ch in ["*", "?", "["])

        if has_glob:
            for match in glob.glob(inp, recursive=True):
                mp = Path(match)
                if mp.is_file():
                    out.append(mp)
            continue

        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    out.append(f)
            continue

        if p.is_file():
            out.append(p)

    # de-dup, stable
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in out:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(p)
    return uniq


def _normalize_level(level: str | None) -> str | None:
    if not level:
        return None
    lv = level.strip().upper()
    if lv == "WARNING":
        return "WARN"
    if lv == "CRITICAL":
        return "FATAL"
    return lv


def _parse_line(line: str) -> RawEvent:
    raw = line.rstrip("\n")
    # JSON line (common structured logs)
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            msg = obj.get("message") or obj.get("msg") or obj.get("error") or raw
            level = obj.get("level") or obj.get("severity")
            service = obj.get("service") or obj.get("app") or obj.get("svc")
            error_code = obj.get("error_code") or obj.get("err_code") or obj.get("code")
            ts = obj.get("timestamp") or obj.get("time") or obj.get("@timestamp")

            return RawEvent(
                raw=raw,
                message=str(msg),
                service=str(service) if service else None,
                level=_normalize_level(str(level)) if level else None,
                timestamp=str(ts) if ts else None,
                error_code=str(error_code) if error_code else None,
                extra=obj,
            )
    except json.JSONDecodeError:
        pass

    # Plain text heuristics
    error_code = None
    m = CODE_KV_RE.search(raw)
    if m:
        error_code = m.group(1)
    else:
        m2 = ERROR_CODE_RE.search(raw)
        if m2:
            error_code = m2.group(0)

    level = None
    lm = LEVEL_RE.search(raw)
    if lm:
        level = _normalize_level(lm.group(1))

    service = None
    sm = SERVICE_KV_RE.search(raw)
    if sm:
        service = sm.group(1)

    ts = None
    tm = ISO_TS_RE.search(raw)
    if tm:
        ts = tm.group(0)

    return RawEvent(
        raw=raw,
        message=raw,
        service=service,
        level=level,
        timestamp=ts,
        error_code=error_code,
        extra=None,
    )


def _categorize_event(
    ev: RawEvent,
    *,
    defaults: Defaults,
    registry: list[RegistryRule],
    rules: list[TextRule],
) -> CategorizedEvent:
    text = ev.message
    if ev.extra:
        # Increase match surface for structured logs
        text = f"{ev.message}\n{json.dumps(ev.extra, ensure_ascii=False)}"

    # 1) Error-code registry wins
    if ev.error_code:
        for r in registry:
            if r.pattern.search(ev.error_code):
                return CategorizedEvent(
                    **ev.__dict__,
                    category=r.category,
                    severity=r.severity,
                    retryable=r.retryable,
                    matched_by="error_code_registry",
                    rule_id=None,
                )

    # 2) Text rules
    for rule in rules:
        if rule.pattern.search(text):
            return CategorizedEvent(
                **ev.__dict__,
                category=rule.category,
                severity=rule.severity,
                retryable=rule.retryable,
                matched_by="rule",
                rule_id=rule.rule_id,
            )

    # 3) Defaults
    return CategorizedEvent(
        **ev.__dict__,
        category=defaults.category,
        severity=defaults.severity,
        retryable=defaults.retryable,
        matched_by="default",
        rule_id=None,
    )


def categorize_logs(
    *,
    config_path: Path,
    inputs: list[str],
    out_dir: Path,
    write_events: bool,
    max_events: int,
) -> None:
    defaults, registry, rules = _load_config(config_path)
    files = _iter_input_files(inputs)

    out_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    total_events = 0

    events_fp = None
    if write_events:
        events_fp = (out_dir / "events.ndjson").open("w", encoding="utf-8")

    try:
        for f in files:
            with f.open("r", encoding="utf-8", errors="replace") as fp:
                for line in fp:
                    if not line.strip():
                        continue

                    raw = _parse_line(line)
                    ev = _categorize_event(raw, defaults=defaults, registry=registry, rules=rules)
                    total_events += 1

                    service = ev.service or "unknown"
                    code = ev.error_code or "NO_CODE"
                    retryable = str(ev.retryable)
                    key = (service, ev.category, ev.severity, retryable, code)

                    slot = groups.get(key)
                    if not slot:
                        slot = {
                            "service": service,
                            "category": ev.category,
                            "severity": ev.severity,
                            "retryable": retryable,
                            "error_code": code,
                            "count": 0,
                            "matched_by": ev.matched_by,
                            "rule_id": ev.rule_id,
                            "samples": [],
                        }
                        groups[key] = slot
                    slot["count"] += 1
                    if len(slot["samples"]) < 3:
                        slot["samples"].append(ev.message[:500])

                    if events_fp:
                        events_fp.write(
                            json.dumps(
                                {
                                    "service": service,
                                    "timestamp": ev.timestamp,
                                    "level": ev.level,
                                    "error_code": ev.error_code,
                                    "category": ev.category,
                                    "severity": ev.severity,
                                    "retryable": ev.retryable,
                                    "matched_by": ev.matched_by,
                                    "rule_id": ev.rule_id,
                                    "message": ev.message,
                                    "raw": ev.raw,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

                    if max_events and total_events >= max_events:
                        break
            if max_events and total_events >= max_events:
                break
    finally:
        if events_fp:
            events_fp.close()

    groups_list = sorted(groups.values(), key=lambda x: (-int(x["count"]), x["service"], x["category"]))

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    report = {
        "generated_at": now,
        "config": str(config_path),
        "inputs": inputs,
        "files": [str(p) for p in files],
        "total_events": total_events,
        "groups": groups_list,
    }

    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with (out_dir / "report.csv").open("w", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(
            fp,
            fieldnames=[
                "service",
                "category",
                "severity",
                "retryable",
                "error_code",
                "count",
                "matched_by",
                "rule_id",
                "sample_1",
                "sample_2",
                "sample_3",
            ],
        )
        w.writeheader()
        for g in groups_list:
            samples = list(g.get("samples") or [])
            w.writerow(
                {
                    "service": g["service"],
                    "category": g["category"],
                    "severity": g["severity"],
                    "retryable": g["retryable"],
                    "error_code": g["error_code"],
                    "count": g["count"],
                    "matched_by": g.get("matched_by"),
                    "rule_id": g.get("rule_id"),
                    "sample_1": samples[0] if len(samples) > 0 else "",
                    "sample_2": samples[1] if len(samples) > 1 else "",
                    "sample_3": samples[2] if len(samples) > 2 else "",
                }
            )

    # A small human-readable summary
    lines: list[str] = []
    lines.append("# ErrorHub Report\n")
    lines.append(f"- generated_at: `{now}`\n")
    lines.append(f"- total_events: **{total_events}**\n")
    lines.append(f"- files: **{len(files)}**\n")
    lines.append("\n## Top groups\n")
    lines.append("| service | category | severity | retryable | error_code | count | matched_by | rule_id |\n")
    lines.append("|---|---|---|---|---|---:|---|---|\n")
    for g in groups_list[:50]:
        lines.append(
            f"| {g['service']} | {g['category']} | {g['severity']} | {g['retryable']} | {g['error_code']} | {g['count']} | {g.get('matched_by','')} | {g.get('rule_id','') or ''} |\n"
        )
    (out_dir / "report.md").write_text("".join(lines), encoding="utf-8")

