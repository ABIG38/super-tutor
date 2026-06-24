# Super-Tutor 项目 AI 生成计划

> **用途**：将此文档逐步喂给 Cursor / Windsurf / Claude Code 等 AI IDE，让 AI 按步骤生成项目代码。
> 每步包含：要执行的精确 Prompt、期望输出文件清单、验证方式。

---

## 📋 总览

| 生成轮次 | 模块 | 预计文件数 | 依赖 |
|----------|------|-----------|------|
| 第 1 轮 | 项目脚手架 + 配置 | 4 个文件 | 无 |
| 第 2 轮 | 文档解析引擎 | 3 个文件 | 第 1 轮 |
| 第 3 轮 | 向量存储 + 索引 | 2 个文件 | 第 1 轮 |
| 第 4 轮 | BM25 关键词检索引擎 | 2 个文件 | 第 1 轮 |
| 第 5 轮 | LLM 客户端 + 溯源 System Prompt | 2 个文件 | 第 1 轮 |
| 第 6 轮 | Agent 编排层 | 2 个文件 | 第 2-5 轮 |
| 第 7 轮 | 规划模块 | 1 个文件 | 第 2、5、6 轮 |
| 第 8 轮 | CLI 主入口 | 1 个文件 | 第 6-7 轮 |
| 第 9 轮 | Streamlit 前端 | 1 个文件 | 第 6 轮 |
| 第 10 轮 | 单元测试 | 2 个文件 | 第 2-5 轮 |

---

## 第 1 轮：项目脚手架 + 配置

### 对 AI IDE 的 Prompt

```
请在 D:\super-turtor 目录下创建以下文件：

1. requirements.txt — Python 依赖清单：
   - langchain>=0.3.0
   - langgraph>=0.2.0
   - openai>=1.50.0
   - PyMuPDF>=1.24.0
   - python-docx>=1.1.0
   - markdown-it-py>=3.0.0
   - chromadb>=0.5.0
   - sentence-transformers>=3.0.0
   - rank-bm25>=0.2.2
   - streamlit>=1.35.0
   - python-dotenv>=1.0.0
   - rich>=13.0.0
   - tiktoken>=0.7.0

2. .env.example — 环境变量模板：
   - LLM_API_KEY=your-api-key-here
   - LLM_API_BASE=https://api.openai.com/v1
   - LLM_MODEL=gpt-4-turbo
   - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   - VECTOR_DB_PATH=./knowledge_base/index/chroma
   - DOCUMENT_STORAGE_PATH=./knowledge_base/raw
   - CHUNK_SIZE=800
   - CHUNK_OVERLAP=150
   - VECTOR_TOP_K=5
   - BM25_TOP_K=5

3. backend/__init__.py — 空包，只有文档字符串 "Super-Tutor Backend Package"

4. backend/config.py — 集中配置模块：
   - 用 python-dotenv 加载 .env
   - 导出 LLM_API_KEY, LLM_API_BASE, LLM_MODEL
   - 导出 EMBEDDING_MODEL
   - 导出 VECTOR_DB_PATH, DOCUMENT_STORAGE_PATH（路径用 pathlib 自动创建）
   - 导出 CHUNK_SIZE=800, CHUNK_OVERLAP=150
   - 导出 VECTOR_TOP_K=5, BM25_TOP_K=5

同时创建以下空目录：
- knowledge_base/raw/
- knowledge_base/index/
- tests/
- frontend/
- backend/document/
- backend/retrieval/
- backend/llm/
- backend/agent/
```

### 期望输出
- `requirements.txt`
- `.env.example`
- `backend/__init__.py`
- `backend/config.py`
- 8 个空子目录

### 验证方式
```bash
pip install -r requirements.txt --dry-run
python -c "from backend.config import LLM_MODEL; print(LLM_MODEL)"
```

---

## 第 2 轮：文档解析引擎

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\backend\document 目录下创建三个文件：

1. __init__.py — 导出 DocumentParser, DocumentChunk, load_document, chunk_document

2. parser.py — DocumentParser 类：
   - 类方法 parse(file_path: str) -> str
   - 支持 PDF (PyMuPDF/fitz), Word (python-docx), Markdown (markdown-it), TXT (直接读)
   - 根据扩展名自动选择解析方式
   - 处理异常时抛出友好的错误信息
   - 额外方法：extract_metadata(file_path) 返回 {filename, pages, size_bytes}

3. splitter.py — 语义切分器：
   - 函数 chunk_document(text: str, metadata: dict) -> list[dict]
   - 使用 LangChain 的 RecursiveCharacterTextSplitter
   - 从 config 读取 CHUNK_SIZE 和 CHUNK_OVERLAP
   - 分隔符优先级：["\n## ", "\n### ", "\n# ", "\n\n", "\n", ". ", "。", " "]
   - 每个 chunk 返回 {"content": str, "metadata": {source, chunk_index, ...}}
   - 在 metadata 中保留原始文档名和 chunk 序号

请写出完整可运行的 Python 代码。
```

### 期望输出
- `backend/document/__init__.py`
- `backend/document/parser.py`
- `backend/document/splitter.py`

### 验证方式
```python
from backend.document import DocumentParser, chunk_document
text = DocumentParser.parse("test.pdf")  # 准备一个测试 PDF
chunks = chunk_document(text, {"filename": "test.pdf"})
assert len(chunks) > 0
assert "content" in chunks[0]
```

---

## 第 3 轮：向量存储 + 索引

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\backend\retrieval 目录下创建：

1. __init__.py — 导出 VectorStore, HybridSearcher

2. vector_store.py — VectorStore 类：
   - __init__(self, persist_dir: str = VECTOR_DB_PATH)
   - 初始化 ChromaDB 客户端，使用 sentence-transformers 的本地 embedding 模型
   - add_chunks(self, chunks: list[dict]) — 将 chunk 列表加入向量库，metadata 保留 {source, chunk_index, text}
   - search(self, query: str, top_k: int = VECTOR_TOP_K) -> list[dict]
   - 返回 {doc_id, content, metadata, score}
   - 支持 persist() 方法保存到磁盘
   - count() 方法返回文档块总数
   - delete_collection() 方法清空

使用 LangChain 的 Chroma wrapper 和 sentence-transformers 的 HuggingFaceEmbeddings。
请写出完整可运行的 Python 代码。
```

### 期望输出
- `backend/retrieval/__init__.py`
- `backend/retrieval/vector_store.py`

### 验证方式
```python
from backend.retrieval.vector_store import VectorStore
vs = VectorStore(persist_dir="./test_chroma")
vs.add_chunks([{"content": "测试文本", "metadata": {"source": "test.txt"}}])
results = vs.search("测试", top_k=1)
assert len(results) > 0
vs.delete_collection()
```

---

## 第 4 轮：BM25 关键词检索引擎

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\backend\retrieval 目录下创建 bm25_search.py：

BM25Searcher 类：
- __init__(self)
- 维护一个 _corpus: list[str]（文档文本列表）和 _metadata: list[dict]
- 使用 rank_bm25 库

方法：
- build_index(self, chunks: list[dict]) -> None
  从 chunks 构建 BM25 索引，分词用 jieba（中文）或空格分词（英文）
  自动检测中英文混用

- search(self, query: str, top_k: int = BM25_TOP_K) -> list[dict]
  返回 BM25 检索结果，每项包含 {content, metadata, score}

- add_chunks(self, chunks: list[dict]) -> None
  增量添加（重建索引）

提示：对于中文分词，使用 jieba.cut；对于英文使用 str.split。
在 requirements.txt 中已预留 jieba 位置，请在代码中用 try/except 优雅降级。
```

### 期望输出
- `backend/retrieval/bm25_search.py`

### 验证方式
```python
from backend.retrieval.bm25_search import BM25Searcher
b = BM25Searcher()
b.build_index([{"content": "线性表是数据结构的基础", "metadata": {"source": "ds.txt"}}])
results = b.search("线性表", top_k=1)
assert len(results) > 0
```

---

## 第 5 轮：LLM 客户端 + 溯源 System Prompt

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\backend\llm 目录下创建：

1. __init__.py — 导出 CitationLLM, CITATION_SYSTEM_PROMPT

2. client.py — CitationLLM 类：
   - __init__(self, model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_API_BASE)
   - 使用 OpenAI 兼容客户端初始化

   - generate_with_citation(self, query: str, retrieved_chunks: list[dict]) -> str
     1. 将检索到的 chunks 格式化进 <context></context> 标签
     2. 拼接 SYSTEM_PROMPT + context + 用户 query
     3. 调用 LLM 生成
     4. 返回带 [来源：文档名] 标记的回答

   - 在代码顶部硬编码 CITATION_SYSTEM_PROMPT 常量：
     "你是一个严谨的学术助手。\n"
     "1. 请优先使用 <context> 标签内的检索内容回答问题。\n"
     "2. 在你的回答中，必须用 [来源文档名：章节名] 标注信息来源。\n"
     "3. 如果 <context> 中的信息不足以回答问题，你可以使用自身知识库补充，\n"
     "   但必须明确声明：'以下内容基于通用知识补充，不在上传文档中：...'\n"
     "4. 禁止编造来源或引用不存在的文档。"

   - _format_context(self, chunks: list[dict]) -> str
     将 chunks 拼接成：
     "<context>\n[来源：{source}]\n{content}\n\n[来源：{source}]\n{content}\n</context>"
```

### 期望输出
- `backend/llm/__init__.py`
- `backend/llm/client.py`

### 验证方式
```python
from backend.llm import CitationLLM, CITATION_SYSTEM_PROMPT
assert "[来源文档名" in CITATION_SYSTEM_PROMPT
```

---

## 第 6 轮：Agent 编排层（核心）

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\backend\agent 目录下创建：

1. __init__.py — 导出 SuperTutorAgent

2. orchestrator.py — SuperTutorAgent 类（核心编排器）：

   这是整个系统的大脑。它使用 LangChain 将各个工具串联起来。

   class SuperTutorAgent:
       def __init__(self):
           # 初始化所有子组件
           self.vector_store = VectorStore()
           self.bm25_searcher = BM25Searcher()
           self.llm = CitationLLM()
           self.documents_indexed = []

       def ingest_document(self, file_path: str) -> str:
           """上传并索引文档"""
           1. 用 DocumentParser.parse(file_path) 解析
           2. 用 chunk_document() 切分
           3. chunks 同时加入 VectorStore 和 BM25Searcher
           4. 返回 "已索引 {N} 个文档块"

       def ask(self, question: str) -> str:
           """问答接口 — 混合检索 + 溯源生成"""
           1. 向量检索 top_k=VECTOR_TOP_K
           2. BM25 检索 top_k=BM25_TOP_K
           3. 合并去重（按 content 哈希）
           4. 按分数排序取 top
           5. 调用 llm.generate_with_citation(question, merged_chunks)
           6. 返回回答

       def list_documents(self) -> list[str]:
           """列出已索引的文档"""
           返回 self.documents_indexed

   工具函数：
   - _merge_and_rerank(vec_results, bm25_results) -> list[dict]
     合并两个检索结果，对同一 chunk 的 content 去重

   LangChain Tool 包装（在文件底部）：
   - 使用 @tool 装饰器包装 ask、ingest_document、list_documents
   - 创建一个 LangChain Agent，可以使用上述工具
   - 创建方法 create_langchain_agent() 返回 AgentExecutor
```

### 期望输出
- `backend/agent/__init__.py`
- `backend/agent/orchestrator.py`

### 验证方式
```python
from backend.agent import SuperTutorAgent
agent = SuperTutorAgent()
# 上传一个测试文本文件
result = agent.ingest_document("test.md")
assert "已索引" in result
answer = agent.ask("这篇文章讲了什么？")
assert len(answer) > 0
```

---

## 第 7 轮：规划模块（Planning Tool）

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\backend\agent 目录下创建 planner.py：

class StudyPlanner:
    """基于已索引教材内容，自动生成复习计划"""

    def __init__(self, orchestrator: SuperTutorAgent):
        self.orchestrator = orchestrator

    def generate_plan(self, days: int, subject: str = None) -> str:
        """
        生成 Markdown 格式的复习计划
        
        流程：
        1. 调用 orchestrator.ask() 检索教材的章节目录
           — 提问："请列出教材的章节目录和每章包含的小节标题"
        2. 再次检索各章的重难点
        3. 计算每天要覆盖的内容量
        4. 用 LLM 生成格式化的 Markdown 计划

        输出格式示例：
        ## 第 1 周：数据结构基础（D1 - D7）
        ### 第 1 天：绪论与算法分析
        - [来源：《数据结构》第1章]
        - 学习内容：时间复杂度、空间复杂度、大O表示法
        - 配套习题：章节课后习题 1.1-1.5
        - 预计用时：2.5小时
        """

    def _query_chapter_list(self) -> str:
        """检索教材章节目录"""

    def _query_key_points(self, chapter: str) -> str:
        """检索某章的重难点"""

    def _format_plan_prompt(self, chapters, key_points, days) -> str:
        """构造规划生成 prompt"""


# 创建 LangChain Tool
from langchain.tools import tool

@tool
def generate_study_plan(days: int, subject: str = "全部") -> str:
    """基于已上传的教材，生成 {days} 天的复习计划"""
    planner = ...  # 需注入 orchestrator 实例
    return planner.generate_plan(days, subject)
```

### 期望输出
- `backend/agent/planner.py`

---

## 第 8 轮：CLI 主入口

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor 目录下创建 main.py — CLI 交互入口：

使用 Python 的标准库 argparse + rich 库实现漂亮的终端界面。

命令：
  python main.py ingest <file_path>     # 上传并索引文档
  python main.py ask "<question>"       # 提问
  python main.py plan --days 30         # 生成复习计划
  python main.py docs                   # 列出已索引文档
  python main.py chat                   # 进入交互对话模式

交互模式（chat 命令）：
- 显示欢迎信息
- 循环输入问题，逐条回答
- 输入 "plan 30" 触发规划
- 输入 "docs" 列出文档
- 输入 "exit" 或 Ctrl+C 退出

使用 rich 美化输出：
- 回答用绿色
- 来源标注用蓝色加粗
- 警告用黄色
```

### 期望输出
- `main.py`

---

## 第 9 轮：Streamlit Web 前端

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\frontend 目录下创建 app.py — Streamlit Web 界面：

页面布局 — 左侧栏 + 主区域：

左侧栏：
- 标题"🧠 超级导师"
- 文件上传区（支持 PDF/Word/MD/TXT）
- 上传按钮，点击后显示索引进度
- 分割线
- "已索引文档"列表
- "清空知识库"按钮

主区域 — 两个 Tab：
1. "💬 问答" Tab：
   - 输入框 + 发送按钮
   - 聊天历史（每条包含用户问题和 AI 回答）
   - AI 回答显示时用 markdown 渲染
   - 引用标注用特殊颜色高亮

2. "📅 规划" Tab：
   - 天数滑块（1-90）
   - 科目选择（可选）
   - "生成计划"按钮
   - 结果用 markdown 渲染

初始化时自动创建 SuperTutorAgent 实例并缓存到 st.session_state
```

### 期望输出
- `frontend/app.py`

---

## 第 10 轮：单元测试

### 对 AI IDE 的 Prompt

```
在 D:\super-turtor\tests 目录下创建：

1. test_document.py — 测试文档解析和切分：
   - test_parse_txt() — 创建临时 txt 文件，测试解析
   - test_parse_markdown() — 测试 MD 解析
   - test_chunk_document() — 测试切分后块数 > 0 且每块有 content
   - test_chunk_preserves_metadata() — 每块有 source 和 chunk_index

2. test_retrieval.py — 测试检索：
   - test_vector_store_add_and_search() — 添加并检索
   - test_bm25_build_and_search() — BM25 索引与检索
   - test_hybrid_merge_dedup() — 混合检索去重
   - test_citation_format() — 回答中包含引用标记

依赖：pytest, tempfile 标准库
使用 setUp 创建临时文档，tearDown 清理。
```

### 期望输出
- `tests/test_document.py`
- `tests/test_retrieval.py`

### 验证方式
```bash
pytest tests/ -v
```

---

## 🔄 生成顺序 & 依赖图

```
第 1 轮 (config)
    │
    ├──► 第 2 轮 (parser/splitter)
    │        │
    ├──► 第 3 轮 (vector_store) ──┐
    │        │                     │
    ├──► 第 4 轮 (bm25) ──────────┤
    │        │                     │
    └──► 第 5 轮 (llm client) ────┤
             │                     │
             └─────────┬───────────┘
                       ▼
                  第 6 轮 (orchestrator)
                       │
                 ┌─────┴─────┐
                 ▼           ▼
            第 7 轮      第 8 轮
           (planner)    (main.py)
                 │           │
                 └─────┬─────┘
                       ▼
                  第 9 轮 (frontend)
                       │
                       ▼
                  第 10 轮 (tests)
```

---

## ⚠️ 注意事项

1. **每轮独立**：每轮 Prompt 都自包含上下文，可以直接复制粘贴到 Cursor Chat
2. **先审后执行**：请先审查每轮的 Prompt，确认符合预期后再让 AI 生成
3. **导入路径**：各模块之间通过 `from backend.xxx import ...` 互相引用
4. **API Key**：生成代码时不需要真实 API Key，`.env.example` 用占位符
5. **第 6 轮最关键**：Orchestrator 是整个系统的中枢，建议重点审查其生成质量
6. **第 5 轮 System Prompt**：硬编码在代码中的溯源规则是防幻觉的核心，生成后请仔细核对

---

*生成日期：2025-06-19 · 供 Cursor/Windsurf 使用*
