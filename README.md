# 语义相似图片检索（图片入库自动打标签）

目标：上传图片后，自动生成 **caption + tags**，并将图片编码为 **embedding** 存入向量库；支持按 **文本/图片/多模态（text+image）** 语义检索相似图；支持 **用户自定义标签** 并参与排序。

## 功能概览

- **入库**：`image -> (BLIP caption) -> tags -> (CLIP embedding) -> FAISS`
- **检索**：`query(text/image/both) -> embedding -> FAISS topN -> 融合排序(含用户标签加分)`
- **多租户**：按 `tenantId` 分开存储索引文件（`data/faiss/<tenant>.faiss`）与图片目录（`data/images/<tenant>/`）
- **离线批处理**：支持本地目录批量入库

## 快速开始

### 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3) 图片入库（自动 caption + tags）

```bash
curl -X POST "http://localhost:8000/v1/ingest" \
  -F tenantId=demo \
  -F image=@/path/to/a.jpg \
  -F 'userTags=["我的标签1","海边","日落"]'
```

### 4) 语义检索（文本/图片/多模态）

文本检索：

```bash
curl -X POST "http://localhost:8000/v1/search" \
  -F tenantId=demo \
  -F topN=5 \
  -F queryText="sunset beach"
```

图片检索：

```bash
curl -X POST "http://localhost:8000/v1/search" \
  -F tenantId=demo \
  -F topN=5 \
  -F queryImage=@/path/to/query.jpg
```

多模态融合（文本+图片一起）：

```bash
curl -X POST "http://localhost:8000/v1/search" \
  -F tenantId=demo \
  -F topN=5 \
  -F queryText="sunset" \
  -F queryImage=@/path/to/query.jpg
```

## API 输出（核心字段）

- **入库返回**：`imageId, tenantId, caption, tags, userTags`
- **检索返回**：`topN 相似图片 + tags + caption + score`

## “用户自定义标签参与排序”的实现方式

当前实现：当 `queryText` 存在时，若查询文本能匹配到某图片的 `userTags`（子串匹配），则给该图片的相似度 **加一个可控 bonus**（见 `app/config.py` 的 `tag_bonus`）。

> 这块是刻意做成可替换的最小实现：你可以把子串匹配替换为 **tag embedding 相似度**、BM25、或业务权重规则（例如“置顶标签”“强制过滤”等）。

## 离线批处理

```bash
python -m scripts.batch_ingest --tenant demo --dir /path/to/images --user-tags "travel,album"
```

## 存储结构

- `data/metadata.sqlite3`：图片元数据（caption/tags/userTags/路径）+ 向量 id 映射
- `data/faiss/<tenant>.faiss`：FAISS 向量索引（cosine via inner-product over normalized vectors）
- `data/images/<tenant>/<imageId>.<ext>`：图片文件落盘

## 模型

- **Embedding（图/文）**：`openai/clip-vit-base-patch32`
- **Caption**：`Salesforce/blip-image-captioning-base`

首次运行会自动从 HuggingFace 下载模型权重（需要可访问的网络环境）。