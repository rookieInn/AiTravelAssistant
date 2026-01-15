# AiTravelAssistant

## Database schema

### `decision_unit`
- `id` (PK)
- `rule_set_ids` (varchar(256))：多个 `rule_set_id` 用 `,` 隔开
- `app_name`

### `rule_set`
- `rule_set_id` (PK)
- `meta` (varchar(5120))
- `rules_order`

DDL: see `db/schema.sql`.