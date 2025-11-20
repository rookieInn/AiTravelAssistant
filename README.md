# AiTravelAssistant

## 清理一年未登录用户在阿里云 OSS 中的图片

仓库提供了脚本 `scripts/cleanup_inactive_oss.py`，用于批量删除超过一定时间未登录用户在 OSS 中的图片资源。脚本默认仅做 Dry-Run，确认无误后可使用 `--apply --yes` 真正执行删除。

### 前置条件
- Python 3.10+
- 数据库中 `users` 表（或自定义查询）包含 `id`, `last_login_at`, `oss_prefix`
- 阿里云 OSS Bucket 访问凭证

### 安装依赖
```bash
pip install -r requirements.txt
```

### 环境变量
在运行脚本前设置以下环境变量（可写入 `.env` 文件）：

| 变量名 | 说明 |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy 兼容的数据库连接串，例如 `mysql+pymysql://user:pass@host:3306/app` |
| `ALIYUN_OSS_ENDPOINT` | OSS 访问域名，例如 `https://oss-cn-hangzhou.aliyuncs.com` |
| `ALIYUN_OSS_ACCESS_KEY_ID` | OSS AccessKey ID |
| `ALIYUN_OSS_ACCESS_KEY_SECRET` | OSS AccessKey Secret |
| `ALIYUN_OSS_BUCKET` | OSS Bucket 名称 |
| `USER_QUERY`（可选） | 自定义 SQL 查询，必须包含 `:cutoff` 参数并返回 `id`, `oss_prefix` |

### 使用方式
```bash
# 先进行 Dry-Run
python scripts/cleanup_inactive_oss.py --older-than-days 365

# 确认后正式删除
python scripts/cleanup_inactive_oss.py --older-than-days 365 --apply --yes
```

如需特殊查询条件，可通过环境变量 `USER_QUERY` 或 `--user-query-file` 指定 SQL，例如：

```sql
SELECT id,
       CONCAT('user_uploads/', id, '/') AS oss_prefix
FROM users
WHERE (last_login_at IS NULL OR last_login_at < :cutoff)
  AND status = 'inactive'
```

脚本会按 `--batch-size`（默认 1000）批量删除前缀下的所有对象，并在日志中输出每个用户删除的对象数量。*** End Patch