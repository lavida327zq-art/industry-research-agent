# 行业调研与报告生成多 Agent 协作系统

基于 **LangChain + LangGraph** 的多 Agent 协作系统，输入一个行业主题，自动完成资料搜集、结构化分析、报告撰写，输出完整的 Markdown 调研报告。

## ✨ 功能特性

- **多 Agent 分工协作**：资料搜集 → 结构化分析 → 报告撰写
- **LLM 自主搜索（ReAct）**：绑定搜索工具，LLM 自主决定搜什么
- **四级降级机制**：LLM自主搜索 → 硬编码搜索 → LLM生成 → 模拟数据
- **Streamlit Web 界面**：实时进度展示、一键ZIP打包下载

## 🚀 快速开始

```bash
# 安装
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key

# 运行
python main.py
# 或 Web 界面
streamlit run app.py
```

## 📁 项目结构

```
├── main.py          # 工作流图组装 + 入口
├── app.py           # Streamlit Web 界面
├── agents.py        # Agent 节点定义
├── prompts.py       # System Prompt 常量
├── state.py         # 共享状态定义
├── requirements.txt # 依赖清单
└── .env.example     # 环境变量模板
```

## 🛠️ 技术栈

LangChain / LangGraph / DeepSeek API / Tavily / Streamlit / Pydantic

## 📜 License

MIT
