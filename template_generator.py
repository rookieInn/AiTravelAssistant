#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from typing import Any, Dict, List


TEMPLATES: Dict[str, Dict[str, Any]] = {
    "email": {
        "label": "邮件模板",
        "required": [
            "to_name",
            "topic",
            "context",
            "request",
            "deadline",
            "sender_name",
            "sender_title",
            "contact",
        ],
        "field_labels": {
            "to_name": "收件人姓名",
            "topic": "主题",
            "context": "背景",
            "request": "需求/请求",
            "deadline": "期望完成时间",
            "sender_name": "发件人姓名",
            "sender_title": "发件人职位/部门",
            "contact": "联系方式",
        },
        "subject": "关于{topic}的沟通",
        "body": (
            "{to_name}您好，\n\n"
            "我想就{topic}与您沟通。\n"
            "背景：{context}\n"
            "需求/请求：{request}\n"
            "期望完成时间：{deadline}\n\n"
            "如需进一步信息，欢迎联系我：{contact}\n\n"
            "谢谢！\n"
            "{sender_name}\n"
            "{sender_title}"
        ),
        "list_fields": [],
    },
    "payment": {
        "label": "催款模板",
        "required": [
            "to_company",
            "contract_no",
            "invoice_no",
            "amount",
            "due_date",
            "sender_name",
            "sender_company",
            "contact",
        ],
        "field_labels": {
            "to_company": "收款方公司",
            "contract_no": "合同编号",
            "invoice_no": "发票号",
            "amount": "金额",
            "due_date": "付款截止日",
            "sender_name": "联系人姓名",
            "sender_company": "联系人公司",
            "contact": "联系方式",
        },
        "subject": "关于{invoice_no}款项的提醒",
        "body": (
            "{to_company}您好，\n\n"
            "根据合同{contract_no}，贵司应付款项如下：\n"
            "发票号：{invoice_no}\n"
            "金额：{amount}\n"
            "付款截止日：{due_date}\n\n"
            "烦请安排付款并告知进度。如已付款请忽略并发送凭证。\n\n"
            "联系人：{sender_name}（{sender_company}），{contact}"
        ),
        "list_fields": [],
    },
    "leave": {
        "label": "请假模板",
        "required": [
            "manager_name",
            "employee_name",
            "leave_type",
            "start_date",
            "end_date",
            "days",
            "reason",
            "backup",
            "contact",
        ],
        "field_labels": {
            "manager_name": "审批人/主管",
            "employee_name": "请假人",
            "leave_type": "请假类型",
            "start_date": "开始日期",
            "end_date": "结束日期",
            "days": "请假天数",
            "reason": "请假原因",
            "backup": "工作交接",
            "contact": "紧急联系方式",
        },
        "subject": "请假申请-{employee_name}-{start_date}",
        "body": (
            "{manager_name}您好，\n\n"
            "我是{employee_name}，申请{leave_type}，时间：{start_date}至{end_date}，共{days}天。\n"
            "原因：{reason}\n"
            "工作交接：{backup}\n"
            "紧急联系：{contact}\n\n"
            "请审批，谢谢。"
        ),
        "list_fields": [],
    },
    "minutes": {
        "label": "会议纪要模板",
        "required": [
            "topic",
            "date",
            "time",
            "location",
            "host",
            "participants",
            "agenda",
            "key_points",
            "decisions",
            "action_items",
            "recorder",
        ],
        "field_labels": {
            "topic": "会议主题",
            "date": "日期",
            "time": "时间",
            "location": "地点",
            "host": "主持人",
            "participants": "参会人员",
            "agenda": "议程",
            "key_points": "讨论要点",
            "decisions": "决议",
            "action_items": "行动项",
            "recorder": "记录人",
        },
        "subject": "会议纪要-{topic}-{date}",
        "body": (
            "主题：{topic}\n"
            "时间：{date} {time}\n"
            "地点：{location}\n"
            "主持：{host}\n"
            "记录：{recorder}\n\n"
            "参会人员：\n"
            "{participants_list}\n\n"
            "议程：\n"
            "{agenda_list}\n\n"
            "讨论要点：\n"
            "{key_points_list}\n\n"
            "决议：\n"
            "{decisions_list}\n\n"
            "行动项：\n"
            "{action_items_list}"
        ),
        "list_fields": ["participants", "agenda", "key_points", "decisions", "action_items"],
    },
    "quote": {
        "label": "报价模板",
        "required": [
            "client_company",
            "project",
            "quote_no",
            "date",
            "validity",
            "items",
            "subtotal",
            "tax_rate",
            "total",
            "payment_terms",
            "sender_name",
            "sender_company",
            "contact",
        ],
        "field_labels": {
            "client_company": "客户公司",
            "project": "项目名称",
            "quote_no": "报价单号",
            "date": "报价日期",
            "validity": "有效期",
            "items": "报价明细",
            "subtotal": "小计",
            "tax_rate": "税率",
            "total": "含税总价",
            "payment_terms": "付款条件",
            "sender_name": "联系人姓名",
            "sender_company": "联系人公司",
            "contact": "联系方式",
        },
        "subject": "报价单-{project}-{date}",
        "body": (
            "{client_company}您好，\n\n"
            "以下为{project}报价（报价单号：{quote_no}，日期：{date}，有效期：{validity}）：\n\n"
            "报价明细：\n"
            "{items_list}\n\n"
            "小计：{subtotal}\n"
            "税率：{tax_rate}\n"
            "含税总价：{total}\n\n"
            "付款条件：{payment_terms}\n"
            "联系人：{sender_name}（{sender_company}），{contact}\n\n"
            "如需调整请告知，谢谢！"
        ),
        "list_fields": ["items"],
    },
}


def format_list(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            return ""
        if "\n" in raw:
            items = [line.strip().lstrip("- ").strip() for line in raw.splitlines() if line.strip()]
        elif "；" in raw:
            items = [item.strip() for item in raw.split("；") if item.strip()]
        elif ";" in raw:
            items = [item.strip() for item in raw.split(";") if item.strip()]
        elif "，" in raw:
            items = [item.strip() for item in raw.split("，") if item.strip()]
        elif "," in raw:
            items = [item.strip() for item in raw.split(",") if item.strip()]
        else:
            items = [raw]
    else:
        items = [str(value).strip()]
    return "\n".join(f"- {item}" for item in items if item)


def parse_set_values(values: List[str]) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"参数格式错误，应为 KEY=VALUE：{item}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"参数格式错误，应为 KEY=VALUE：{item}")
        data[key] = value
    return data


def list_templates() -> None:
    print("可用模板：")
    for key, meta in TEMPLATES.items():
        print(f"- {key}: {meta['label']}")
        labels = meta.get("field_labels", {})
        required = meta.get("required", [])
        for field in required:
            label = labels.get(field, field)
            print(f"    * {field}: {label}")


def prompt_missing_fields(data: Dict[str, Any], required: List[str], labels: Dict[str, str]) -> None:
    for field in required:
        if data.get(field):
            continue
        label = labels.get(field, field)
        value = input(f"{label} ({field}): ").strip()
        if value:
            data[field] = value


def render_template(template_key: str, data: Dict[str, Any]) -> str:
    meta = TEMPLATES[template_key]
    render_data = dict(data)
    for field in meta.get("list_fields", []):
        render_data[f"{field}_list"] = format_list(render_data.get(field, ""))
    subject = meta["subject"].format_map(render_data).strip()
    body = meta["body"].format_map(render_data).strip()
    return f"主题：{subject}\n\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="快速生成常用邮件/文档模版（邮件、催款、请假、会议纪要、报价）"
    )
    parser.add_argument("--list", action="store_true", help="列出可用模板和字段")
    parser.add_argument(
        "--type",
        dest="template_type",
        choices=sorted(TEMPLATES.keys()),
        help="模板类型",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="设置字段值，可重复使用",
    )
    parser.add_argument("--data", help="JSON 格式的字段数据")
    parser.add_argument("--interactive", action="store_true", help="交互式补全缺失字段")
    parser.add_argument("--output", help="输出到文件，默认输出到标准输出")

    args = parser.parse_args()

    if args.list:
        list_templates()
        return 0

    if not args.template_type:
        parser.print_help()
        return 2

    data: Dict[str, Any] = {}
    if args.data:
        try:
            payload = json.loads(args.data)
        except json.JSONDecodeError as exc:
            print(f"JSON 解析失败：{exc}", file=sys.stderr)
            return 2
        if not isinstance(payload, dict):
            print("JSON 数据必须是对象字典", file=sys.stderr)
            return 2
        data.update(payload)

    try:
        data.update(parse_set_values(args.set))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    meta = TEMPLATES[args.template_type]
    required = meta.get("required", [])
    labels = meta.get("field_labels", {})

    if args.interactive:
        prompt_missing_fields(data, required, labels)

    missing = [field for field in required if not data.get(field)]
    if missing:
        print("缺少字段：" + ", ".join(missing), file=sys.stderr)
        print("可使用 --list 查看字段说明或加 --interactive 交互补全。", file=sys.stderr)
        return 2

    try:
        content = render_template(args.template_type, data)
    except KeyError as exc:
        print(f"字段缺失：{exc}", file=sys.stderr)
        return 2

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(content)
    else:
        print(content, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
