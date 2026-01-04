# ErrorHub Report
- generated_at: `2026-01-04T10:45:46.690495+00:00`
- total_events: **11**
- files: **2**

## Top groups
| service | category | severity | retryable | error_code | count | matched_by | rule_id |
|---|---|---|---|---|---:|---|---|
| order-service | NETWORK | P1 | True | NO_CODE | 1 | rule | network |
| order-service | RATE_LIMIT | P2 | True | NO_CODE | 1 | rule | rate_limit |
| order-service | RUNTIME | P0 | unknown | NO_CODE | 1 | rule | runtime |
| order-service | TIMEOUT | P1 | True | NO_CODE | 1 | rule | timeout |
| order-service | UNKNOWN | P2 | unknown | NO_CODE | 1 | default |  |
| order-service | VALIDATION | P4 | False | ORDER-API-1001 | 1 | error_code_registry |  |
| pay-service | AUTHENTICATION | P3 | False | NO_CODE | 1 | rule | auth |
| pay-service | DEPENDENCY | P1 | True | PAY-GW-4002 | 1 | error_code_registry |  |
| pay-service | NETWORK | P1 | True | NO_CODE | 1 | rule | network |
| pay-service | RESOURCE_EXHAUSTED | P0 | unknown | NO_CODE | 1 | rule | resource_exhausted |
| pay-service | TIMEOUT | P1 | True | NO_CODE | 1 | rule | timeout |
