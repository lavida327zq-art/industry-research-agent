# 行业调研与报告生成多 Agent 协作系统

基于 **LangChain + LangGraph** 的多 Agent 协作系统，输入一个行业主题，自动完成资料搜集、结构化分析、报告撰写，输出一份完整的 Markdown 调研报告。

***

## ✨ 功能特性

- **多 Agent 分工协作**：资料搜集 → 结构化分析 → 报告撰写，全自动流转
- **智能路由调度**：Supervisor 使用 LLM 评估全局状态，动态决定下一步节点
- **System Prompt 驱动**：4 个 Agent 各自绑定专业化提示词，职责清晰
- **LLM 自主搜索（ReAct）**：research_agent 将 Tavily 搜索工具绑定到 LLM（`bind_tools`），由 LLM 自主决定搜什么关键词、搜几次、保留哪些结果，适应不同主题的调研需求
- **结构化输出**：自动提炼核心趋势、SWOT 分析、关键数据指标
- **标准报告格式**：输出包含摘要、行业现状、SWOT、未来建议的 Markdown 报告
- **四级降级机制**：LLM 自主搜索 → 硬编码多维度搜索 → LLM 生成 → 模拟数据，配置即用、无网也能跑
- **报告持久化**：运行结束后自动将 3 份 Markdown 文档保存到 `reports/` 目录
- **Streamlit Web 界面**：浏览器中配置主题、实时观察执行进度（显示搜索轮次与关键词）、在线渲染与一键打包下载（ZIP）
- **C 端友好体验**：面向普通用户设计，无编程术语，操作简单，实时反馈清晰
- **环境隔离**：基于 `.venv` 虚拟环境，依赖互不污染

***

## 🏗️ 系统架构

```
用户输入主题 → Supervisor 路由
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   资料搜集      结构化分析     报告撰写
  (Researcher)  (Analyst)    (Writer)
       │            │            │
       └───── 共享状态 ──────────┘
                    │
                    ▼
              Supervisor 决策 → 下一节点 / 结束
```

**4 个 Agent 角色**：

| Agent              | 职责                                  |
| ------------------ | ----------------------------------- |
| `research_agent`   | LLM 自主搜索（ReAct）：动态规划搜索维度、生成查询词、筛选结果 |
| `analyst_agent`    | 提炼核心趋势、SWOT 关键点、数据指标                |
| `writer_agent`     | 撰写 Markdown 格式调研报告                  |
| `supervisor_agent` | 路由决策，根据数据完整度自动跳转或结束                 |

***

## 📦 输出示例

输入主题 `2026年新能源汽车出海趋势`，输出报告结构：

```
# 「2026年新能源汽车出海趋势」行业调研报告

## 一、摘要
## 二、行业现状
    2.1 关键数据指标（市场规模 / CAGR / 市场份额）
    2.2 核心趋势
    2.3 原始资料摘要
## 三、SWOT 分析
    3.1 优势 Strengths
    3.2 劣势 Weaknesses
    3.3 机会 Opportunities
    3.4 威胁 Threats
## 四、未来建议
```

***

## 🚀 快速开始

### 环境要求

- Python 3.10+
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/api_keys)），也可不配置直接用模拟模式运行
- Tavily API Key（[申请地址](https://tavily.com)，免费 1000 次/月），未配置则 research_agent 降级到 LLM 生成

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd 行业调研与报告生成多agent协作系统

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

### 运行

**方式一：命令行**

```bash
source .venv/bin/activate
python main.py
```

运行后将逐步打印 7 步流转日志，并将报告保存到 `reports/` 目录。

**方式二：Web 界面（推荐）**

```bash
source .venv/bin/activate
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`，在左侧输入调研主题 → 点击「开始调研」→ 实时观察 AI 搜集资料/分析/撰写的进度（含搜索轮次与关键词）→ 在线查看报告，一键下载全部材料（ZIP 打包 3 个 Markdown 文档）。

***

## 📁 项目结构

```
├── main.py              # 入口脚本：工作流图组装 + 运行 + 文件保存
├── app.py               # Streamlit Web 界面（后台线程 + 实时进度 + Markdown 渲染）
├── agents.py            # Agent 节点：research（ReAct 自主搜索）/ analyst / writer / supervisor
├── prompts.py           # System Prompt 常量定义
├── state.py             # 共享状态定义：ResearchState
├── requirements.txt     # 依赖清单
├── .env.example         # 环境变量模板
├── reports/             # 生成的报告与产物（动态生成，不入库）
│   ├── {主题_时间戳}_报告.md       # 最终 Markdown 调研报告
│   ├── {主题_时间戳}_原始资料.md    # 搜集到的原始资料
│   └── {主题_时间戳}_分析摘要.md    # 数据提炼与观点摘要
└── .gitignore
```

***

## 🛠️ 技术栈

| 技术                                                             | 用途                                  |
| -------------------------------------------------------------- | ----------------------------------- |
| [LangChain](https://python.langchain.com/)                     | LLM 调用、Prompt 管理、工具绑定（`bind_tools`） |
| [LangGraph](https://langchain-ai.github.io/langgraph/)         | 多 Agent 状态图编排                       |
| [langchain-tavily](https://pypi.org/project/langchain-tavily/) | Tavily 搜索工具集成（供 ReAct 调用）           |
| [Pydantic](https://docs.pydantic.dev/)                         | 共享状态类型校验                            |
| [python-dotenv](https://pypi.org/project/python-dotenv/)       | 环境变量加载                              |
| [DeepSeek API](https://api-docs.deepseek.com/zh-cn/)           | 大模型服务（兼容 OpenAI 格式，支持 tool calling） |
| [Streamlit](https://streamlit.io/)                             | Web 界面框架（后台线程 + 实时进度 + Markdown 渲染） |

***

## 📄 文档

- [开发日志.md](./开发日志.md) — 项目演进记录与开发细节
- [开发知识QA.md](./开发知识QA.md) — 开发过程中的知识点问答汇总

***

## 📌 路线图

- [x] 多 Agent 工作流编排（StateGraph + 条件边路由）
- [x] 模拟数据驱动的完整流程验证
- [x] 虚拟环境与配置管理
- [x] System Prompt 定义 + LLM 链绑定机制
- [x] 接入 Tavily 搜索工具（硬编码多维度搜索）
- [x] 报告持久化（保存为 Markdown 到 `reports/` 目录）
- [x] LLM 自主搜索（ReAct：`bind_tools` + 手动循环，替代硬编码搜索）
- [x] Streamlit Web 界面（后台线程 + 实时进度 + Markdown 渲染）
- [x] LLM 超时保护 + UI 实时进度反馈（防界面卡死）
- [x] 跨线程状态传递修复（session_state 字典引用 + 线程锁）
- [x] 输出文件统一为 Markdown + 一键 ZIP 打包下载
- [x] C 端友好化改造（去除技术术语、placeholder 提示、友好文案）
- [x] 结构化输出解析（Pydantic with_structured_output）
- [ ] 错误处理与重试机制
- [ ] 流式输出（报告生成过程流式打印）

***

## 📜 License

MIT
