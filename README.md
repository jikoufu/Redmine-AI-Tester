# 🚀 Redmine AI Helper (TestDev Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek--V3-green.svg)](https://www.deepseek.com/)

> **让 AI 成为你的测开助手。** 这是一个基于 **DeepSeek-V3** 和 **FAISS 向量数据库** 深度定制的 Redmine 辅助分析工具。它旨在解决传统测试分析中“信息碎片化”的痛点，通过 RAG 技术自动从海量 Issue 中提取测试价值。



---

## ✨ 核心能力 | Core Features

* **🔍 穿透式关联分析 (Recursive Context Fetching)**
  - 不同于常规 AI 只能看到单个 Issue，本工具支持自动爬取主任务下的所有“关联任务”和“子任务”。
  - 自动整合历史评论（Journals），消除信息差，挖掘隐藏在讨论记录中的技术风险。

* **📂 智能同步逻辑 (Smart Sync)**
  - **批量同步**：全量分页抓取，快速建立本地项目知识库。
  - **点名入库**：支持通过特定 ID 强制更新，确保向量库与 Redmine 状态实时同步。

* **📝 测开专家报告 (Automated Test Strategy)**
  - 一键生成 Markdown 格式的深度测试报告。
  - **异常链路自动推导**：基于业务逻辑和通用测试原则，自动发现潜在的边界 Bug。
  - **影响范围评估**：智能识别接口、数据库变更对现有系统的冲击。

* **💬 语义检索咨询 (Knowledge RAG)**
  - 基于 FAISS 的本地向量库，支持对全量 Issue 进行自然语言提问。
  - 示例：*“支付模块最近三个月有哪些逻辑变更？”* 或 *“查询权限控制的讨论历史。”*

---

## 🛠️ 快速开始 | Quick Start

### 1. 环境准备

确保 Python $\ge$ 3.9，安装依赖：

```bash
# 建议先安装微软 C++ 运行库 (Windows 必选)
pip install -r requirements.txt