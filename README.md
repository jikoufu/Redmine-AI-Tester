# 🚀 Redmine AI Helper (TestDev Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek--V3-green.svg)](https://www.deepseek.com/)

> **让 AI 成为你的测开大脑。** 这是一个基于 **DeepSeek-V3** 和 **FAISS 向量数据库** 构建的 Redmine 深度分析工具。它通过 RAG (检索增强生成) 技术，自动从海量 Issue 中提取测试价值，生成的不仅仅是总结，更是可以直接落地的自动化测试方案。



---

## ✨ 核心能力 | Key Features

### 🔍 1. 穿透式关联分析 (Recursive Context Fetching)
* **打破信息孤岛**：不同于常规 AI 只能看到单个 Issue，本工具支持自动爬取主任务下的所有“关联任务”和“子任务”。
* **全量上下文**：自动整合描述、历史讨论记录（Journals），消除信息差，挖掘隐藏在长篇讨论中的技术风险点。

### 📝 2. 自动化测开报告 (Option 2)
* **深度逻辑推导**：基于测开专家思维，自动补充 API 边界值、并发风险、权限校验等异常测试路径。
* **来源溯源**：报告中的每个测试点都会标注来源（如：*来源: Issue #87922* 或 *来源: 逻辑推导*），确保结论可靠。
* **存档友好**：自动生成 Markdown 报告并保存至 `temp_md/`，同时自动复制到剪贴板。

### 🌐 3. 全局语义咨询 (Knowledge RAG - Option 3)
* **语义检索**：利用 FAISS 本地向量库，支持对全量 Issue 进行自然语言对话。
* **项目大脑**：问 AI：*“购物车相关的 API 有哪些逻辑变更？”* 或 *“查询权限控制的决策历史。”* 无需手动翻阅数百个页面。

### 📂 4. 智能同步逻辑 (Smart Sync)
* **批量同步**：全量分页抓取，快速建立本地项目知识库。
* **点名入库**：支持通过特定 ID 强制更新单条 Issue，确保向量库的时效性。

---

## 🏗️ 架构思路 | Architecture

本项目采用了典型的 **RAG (Retrieval-Augmented Generation)** 架构：
1. **Extraction (ETL)**: 通过 Redmine API 递归抓取任务树。
2. **Cleaning**: 智能过滤无意义的状态流转记录，保留核心技术讨论。
3. **Vectorization**: 使用文本向量化模型存入本地 FAISS 索引。
4. **Generation**: 结合 DeepSeek-V3 的长上下文能力进行深度逻辑分析。

---

## 🛠️ 快速开始 | Quick Start

### 1. 环境准备

确保 Python $\ge$ 3.9，安装依赖：

```bash
# Windows 用户建议先安装微软 C++ 运行库
pip install -r requirements.txt

```

### 2. 配置文件

在根目录创建 `.env` 文件（已在 `.gitignore` 中排除）：

```env
# Redmine 访问配置
REDMINE_URL=[https://redmine.your-domain.com](https://redmine.your-domain.com)
REDMINE_API_KEY=your_redmine_api_key

# LLM 配置 (支持 DeepSeek/DashScope)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=[https://api.deepseek.com](https://api.deepseek.com)

```

### 3. 运行助手

```bash
python main.py

```

---

## 📖 菜单指南 | Menu Guide

| 选项 | 名称 | 核心逻辑 | 解决的痛点 |
| --- | --- | --- | --- |
| **1** | **全量同步** | 分页抓取 + Embedding | 初始化知识库，解决搜索不精准问题。 |
| **2** | **深度分析** | 穿透抓取 + 异常推导 | **推荐！** 解决复杂任务分析不全、漏测异常链路问题。 |
| **3** | **全局咨询** | RAG 检索 + LLM 总结 | 解决项目历史文档散乱、技术细节难以追溯问题。 |
| **4** | **精准更新** | 单条抓取 + 索引合并 | 解决向量库时效性问题，无需重跑全量同步。 |

---

## ⚠️ 安全与隐私 | Security & Privacy

* **数据本地化**：向量数据库（`index/`）仅存储在本地，不上传云端。
* **脱敏处理**：在生成报告时，AI 会尝试识别并对敏感密钥进行脱敏。
* **免责声明**：AI 生成的建议仅供参考，核心测试决策请结合实际业务逻辑确认。

---

## 🤝 贡献 | Contributing

欢迎提交 Issue 或 Pull Request！你可以通过修改 `src/ai_engine.py` 中的 `SYSTEM_PROMPT` 来定制属于你团队的测试风格。

---

## 📄 开源协议 | License

本项目基于 [MIT License](https://www.google.com/search?q=LICENSE) 开源。


## 项目结构

```
redmine-ai-helper/
├── main.py                    # 程序入口，主菜单交互
├── .env.example               # 环境变量配置模板
├── requirements.txt
│
├── src/
│   ├── core/                  # 核心业务逻辑
│   │   ├── ai_engine.py       # AI 引擎（多角色 Prompt 管理）
│   │   ├── session.py         # 会话 / 历史记录管理
│   │   ├── analyze_flow.py    # 流程：分析 Issue → 生成报告
│   │   ├── chat_flow.py       # 流程：自由多轮对话
│   │   ├── history_flow.py    # 流程：查看 / 继续历史记录
│   │   └── batch_flow.py      # 流程：批量多 Issue 汇总分析
│   │
│   ├── roles/                 # 角色 Prompt 定义（每个角色一个文件）
│   │   ├── __init__.py
│   │   ├── qa.py              # 测试开发工程师
│   │   ├── pm.py              # 产品经理
│   │   ├── dev.py             # 开发工程师
│   │   └── base.py            # 角色基类（新增角色继承此类）
│   │
│   ├── search/                # 搜索模块
│   │   ├── __init__.py
│   │   ├── searcher.py        # 搜索调度器（联合 / 单独模式）
│   │   ├── redmine_search.py  # Redmine 实时关键字搜索
│   │   ├── vector_search.py   # 本地向量库语义搜索
│   │   └── search_flow.py     # 流程：搜索 → 展示 → 跳转分析
│   │
│   ├── sync/                  # 数据同步模块
│   │   ├── __init__.py
│   │   ├── redmine_client.py  # Redmine API 客户端
│   │   ├── vector_store.py    # 向量库管理（FAISS）
│   │   └── sync_flow.py       # 流程：全量 / 增量同步
│   │
│   ├── export/                # 导出模块
│   │   ├── __init__.py
│   │   ├── exporter.py        # 导出调度器
│   │   ├── markdown_export.py # 导出为 Markdown 文件
│   │   ├── clipboard.py       # 复制到剪贴板
│   │   └── redmine_comment.py # 回写到 Redmine 评论区（未实现）
│   │
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── privacy_guard.py   # 隐私脱敏
│       └── logger.py          # 日志配置
│
├── tests/                     # 单元测试
│   ├── test_core/
│   ├── test_search/
│   └── test_sync/
│
├── index/                     # 本地 FAISS 向量库（自动生成）
├── temp_md/                   # 报告 / 对话记录输出目录
└── logs/                      # 运行日志
```
