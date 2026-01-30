import json
from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Tuple


def _unique_keep_order(values: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        v = (v or "").strip()
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def merge_positions_person_list(person_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将 PERSON 列表里同一公司(ENTNAME)+同一人(PERNAME)的多条职位合并：
    - POSITION 用中文逗号“，”连接
    - 去重并保留首次出现顺序
    - 其余字段以首条记录为准
    """
    grouped: "OrderedDict[Tuple[str, str], Dict[str, Any]]" = OrderedDict()
    positions_map: Dict[Tuple[str, str], List[str]] = {}

    for row in person_list or []:
        ent = (row.get("ENTNAME") or "").strip()
        name = (row.get("PERNAME") or "").strip()
        key = (ent, name)
        if key not in grouped:
            grouped[key] = dict(row)  # copy
            positions_map[key] = []
        positions_map[key].append(row.get("POSITION") or "")

    for key, base in grouped.items():
        merged_positions = _unique_keep_order(positions_map.get(key, []))
        base["POSITION"] = "，".join(merged_positions)
        # 如果你希望 POSITIONCODE 也合并，可启用以下逻辑（同样中文逗号拼接）：
        # codes = _unique_keep_order((r.get("POSITIONCODE") or "") for r in rows)
        # base["POSITIONCODE"] = "，".join(codes)

    return list(grouped.values())


def main() -> None:
    # 这里用你给的 PERSON 片段做演示：鲍涛在同一公司担任“副董事长”和“经理”
    sample_person = [
        {"PERNAME": "张军", "POSITION": "董事长", "ENTNAME": "北京中数智汇科技股份有限公司"},
        {"PERNAME": "鲍涛", "POSITION": "副董事长", "ENTNAME": "北京中数智汇科技股份有限公司"},
        {"PERNAME": "鲍涛", "POSITION": "经理", "ENTNAME": "北京中数智汇科技股份有限公司"},
        {"PERNAME": "苏希江", "POSITION": "监事", "ENTNAME": "北京中数智汇科技股份有限公司"},
    ]

    merged = merge_positions_person_list(sample_person)
    print(json.dumps(merged, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

