# 🧠 超级导师 Super-Tutor

<p align="center">
  <img src="https://img.shields.io/badge/status-active-success" alt="Status">
  <img src="https://img.shields.io/badge/python-3.11+-orange" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-0.3+-green" alt="LangChain">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License">
</p>

<p align="center">
  <b>无幻觉 · 超长上下文 · 带溯源的学业/考研规划 Agent</b>
  <br>
  <em>将教材与真题一次性塞入 AI，为每一位学生生成真正可信的个性化复习方案</em>
</p>

---

## 📖 项目简介

超级导师（Super-Tutor）是一款基于 **LangChain + 超长上下文 LLM** 的智能学业/考研规划助手。

不同于通用聊天机器人，它聚焦于**专业课教材与真题的深度理解**——你可以直接把数据结构、计算机组成原理等厚重教材和历年真题上传给系统，系统会：

- **🤖 精准问答**：基于你的教材内容回答知识点问题，并标注信息来源
- **📚 个性化规划**：根据教材目录、重难点和你的时间安排，自动生成复习计划
- **✅ 杜绝幻觉**：所有回答强制溯源，未知内容明确声明"通用知识补充"

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔗 **超长上下文** | 利用云端 LLM 的百万 Token 上下文窗口，一次载入多本教材 |
| 🏷️ **强制溯源** | 每条回答标注 `[来源文档：章节]`，杜绝无中生有 |
| 🎯 **混合检索** | 向量语义检索 + BM25 关键词检索，专业术语精准匹配 |
| 🚀 **Context Caching** | 缓存教材内容，极速响应重复查询，节省 Token 费用 |
| 📅 **智能规划** | 基于真实教材章节目录生成按天/周拆解的复习计划 |
| 💾 **数据本地化** | 向量数据库、索引文件全在本地，隐私无忧 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面 (CLI / Streamlit Web)             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      Orchestrator (Agent)                        │
│                   LangChain Agent 编排层                          │
│     (路由到文档处理 / 检索 / 规划 等工具)                          │
└────┬──────────┬──────────────┬──────────────────┬───────────────┘
     │          │              │                  │
┌────▼───┐ ┌───▼──────┐ ┌─────▼──────┐  ┌───────▼────────┐
│  文档    │ │  检索     │ │  规划       │  │  对话管理        │
│  引擎    │ │  引擎     │ │  引擎       │  │  (上下文/记忆)    │
└────┬───┘ └───┬──────┘ └─────┬──────┘  └───────┬────────┘
     │          │              │                  │
┌────▼──────────▼──────────────▼──────────────────▼─────────────┐
│                       基础设施层                                 │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │ ChromaDB │  │ 文件系统      │  │ LLM API (超长上下文)     │   │
│  │ / FAISS  │  │ (原始文档)    │  │ + Context Caching       │   │
│  └──────────┘  └──────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

系统由 **三大核心模块** 构成：

### 1️⃣ 文件处理与超长上下文引擎
文档上传 → 语义切分（按章节/段落） → 向量化存储 → 上下文缓存预热

### 2️⃣ 无幻觉带溯源的检索系统
混合检索（Vector + BM25） → 结果融合 → LLM 强制溯源生成

### 3️⃣ Agent 规划模块
教材分析 → 时间拆解 → 按周/天生成计划 → 动态调整

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **开发环境** | Cursor / Windsurf (AI IDE) |
| **核心框架** | Python 3.11+ · LangChain |
| **LLM** | 支持 1M+ Token 窗口的云端大模型（含 Context Caching） |
| **向量数据库** | ChromaDB / FAISS |
| **文档解析** | PyMuPDF · python-docx · markdown-it |
| **关键词检索** | rank-bm25 |
| **Web 界面** | Streamlit（可选） |

---

## 📁 项目结构

```
super-tutor/
├── 📂 backend/                  # 后端代码
│   ├── agent/                   # LangChain Agent 编排
│   │   ├── orchestrator.py      # Agent 主路由
│   │   ├── document_tool.py     # 文档处理工具
│   │   ├── retrieval_tool.py    # 检索工具
│   │   └── planning_tool.py     # 规划工具
│   ├── document/                # 文档引擎
│   │   ├── parser.py            # 文档解析器
│   │   ├── splitter.py          # 语义切分器
│   │   └── indexer.py           # 索引构建
│   ├── retrieval/               # 检索引擎
│   │   ├── vector_store.py      # 向量数据库操作
│   │   ├── bm25_search.py       # BM25 关键词检索
│   │   └── hybrid_search.py     # 混合检索融合
│   ├── llm/                     # LLM 交互
│   │   ├── client.py            # API 客户端
│   │   └── caching.py           # Context Caching
│   └── config.py                # 全局配置
├── 📂 frontend/                 # Web 前端（Streamlit）
│   ├── app.py                   # 主应用
│   ├── pages/                   # 多页面
│   │   ├── chat.py
│   │   ├── documents.py
│   │   └── plan.py
│   └── components/              # 可复用组件
├── 📂 knowledge_base/           # 用户上传文档存储
│   ├── raw/                     # 原始文档
│   └── index/                   # 索引文件
├── 📂 tests/                    # 测试
│   ├── test_retrieval.py
│   └── test_planning.py
├── 📄 项目需求说明书.md          # 项目需求文档
├── 📄 README.md                 # 本文件
├── 📄 requirements.txt          # Python 依赖
└── 📄 .env.example              # 环境变量示例
```

---

## 🚀 快速开始

### 前置条件

- Python 3.11+
- 一个支持超长上下文的 LLM API Key（如 DeepSeek、Gemini 等）

### 安装

```bash
# 克隆项目
git clone <your-repo-url>
cd super-tutor

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 使用

```bash
# CLI 模式
python main.py

# Web 模式（Streamlit）
streamlit run frontend/app.py
```

### 上传教材并提问

```
> 上传教材：数据结构（C语言版）.pdf
> 上传成功！开始索引...
> 索引完成，可开始对话。
>
> 提问：什么是时间复杂度？如何计算？
>
> 回答：
> 时间复杂度是衡量算法执行时间随输入规模增长的增长率...
> [来源：《数据结构（C语言版）》第1章 第1.2节]
```

---

## 📊 项目里程碑

| 里程碑 | 内容 | 周期 |
|--------|------|------|
| M1 基础框架 | LangChain Agent 骨架、CLI 交互 | 1 周 |
| M2 文档引擎 | 文档上传/解析/切分/索引 | 1 周 |
| M3 检索问答 | 混合检索 + 溯源生成 | 1-2 周 |
| M4 缓存加速 | Context Caching 接入 | 0.5 周 |
| M5 规划模块 | 复习计划自动生成 | 1 周 |
| M6 Web 界面 | Streamlit 前端 | 1 周 |
| M7 测试优化 | 幻觉率评估、性能调优 | 1 周 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！请确保：

1. 代码通过现有测试 (`pytest tests/`)
2. 新功能附带测试用例
3. 文档同步更新

---

## 📄 许可证

[MIT License](LICENSE)

---

## 🙏 致谢

- LangChain 社区
- 所有提供建议的用户和贡献者
