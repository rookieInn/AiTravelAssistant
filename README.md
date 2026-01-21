# 邮件/文档模版自动生成器

通过命令行快速生成常见的邮件与文档模版，包括：

- 邮件模版（通用商务邮件）
- 催款邮件
- 请假申请
- 会议纪要
- 报价单

## 环境要求

- Python 3.8 及以上

## 快速开始

列出可用模版与字段：

```bash
python template_generator.py --list
```

### 邮件模版

```bash
python template_generator.py --type email \
  --set to_name=李经理 \
  --set topic=需求确认 \
  --set context=本周已完成初版方案整理 \
  --set request=请确认范围与优先级 \
  --set deadline=2026-01-25 \
  --set sender_name=张三 \
  --set sender_title=产品经理 \
  --set contact=zhangsan@example.com
```

### 催款邮件

```bash
python template_generator.py --type payment \
  --set to_company=某某科技 \
  --set contract_no=HT2026-001 \
  --set invoice_no=FP2026-008 \
  --set amount=¥12,800 \
  --set due_date=2026-01-31 \
  --set sender_name=张三 \
  --set sender_company=ABC服务有限公司 \
  --set contact=13800000000
```

### 请假申请

```bash
python template_generator.py --type leave \
  --set manager_name=李经理 \
  --set employee_name=王五 \
  --set leave_type=年假 \
  --set start_date=2026-02-01 \
  --set end_date=2026-02-03 \
  --set days=3 \
  --set reason=家庭事务 \
  --set backup=已与赵六完成交接 \
  --set contact=微信/电话
```

### 会议纪要

列表字段可用 `;`、`，` 或换行分隔。

```bash
python template_generator.py --type minutes \
  --set topic=项目启动会 \
  --set date=2026-01-21 \
  --set time=10:00-11:00 \
  --set location=会议室A \
  --set host=李经理 \
  --set participants="张三;李四;王五" \
  --set agenda="目标说明;里程碑;风险讨论" \
  --set key_points="需求范围确认;资源安排" \
  --set decisions="下周输出PRD;本周完成里程碑计划" \
  --set action_items="张三-输出PRD-1/24;李四-资源排期-1/23" \
  --set recorder=王五
```

### 报价单

```bash
python template_generator.py --type quote \
  --set client_company=XX公司 \
  --set project=官网改版 \
  --set quote_no=Q-2026-001 \
  --set date=2026-01-21 \
  --set validity=30天 \
  --set items="需求调研 1项 - ¥5,000; 设计 1项 - ¥12,000; 开发 1项 - ¥30,000" \
  --set subtotal=¥47,000 \
  --set tax_rate=6% \
  --set total=¥49,820 \
  --set payment_terms=签约30%，验收70% \
  --set sender_name=张三 \
  --set sender_company=某某科技 \
  --set contact=zhangsan@example.com
```

## 交互式补全

如果不想一次性输入所有字段，可加 `--interactive`：

```bash
python template_generator.py --type leave --interactive
```

## 输出到文件

```bash
python template_generator.py --type payment --set ... --output output.txt
```