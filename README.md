# 长文本摘要（中文）

本仓库提供一个**离线可用**的长文本摘要工具：对长中文文本做**抽取式摘要**（TextRank 思路：句子相似度 + PageRank），输出若干关键句拼接成摘要。

## 安装

```bash
python3 -m pip install -r requirements.txt
```

## 使用（命令行）

- **从文件生成摘要**：

```bash
python3 summarize.py your.txt -k 5
```

- **从 stdin 生成摘要**：

```bash
echo "很长的文本..." | python3 -m long_text_summarization -k 3 --max-chars 200
```

常用参数：

- `-k/--max-sentences`：摘要最多保留多少句（默认 3）
- `--max-chars`：摘要字符数软限制（会尽量不超过）
- `--ratio`：按比例保留句子（如 `0.1` 表示保留前 10% 句子）

## 作为库调用（Python）

```python
from long_text_summarization import summarize

text = "这里放你的长文本……"
print(summarize(text, max_sentences=3, max_chars=200))
```