import os, re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

_ENV = Path(__file__).parent/".env"
if _ENV.exists():
    load_dotenv(_ENV)
    print(f"[env] {'已配置' if os.getenv('DEEPSEEK_API_KEY') else '未配置'}")

from langgraph.graph import StateGraph, END
from state import ResearchState
from agents import research, analyst, writer, supervisor, route_after

def _sup_node(state): return {"next_agent": supervisor(state)}

def build():
    wf = StateGraph(ResearchState)
    wf.add_node("supervisor",_sup_node)
    wf.add_node("research",research)
    wf.add_node("analyst",analyst)
    wf.add_node("writer",writer)
    wf.set_entry_point("supervisor")
    wf.add_conditional_edges("supervisor",route_after,{"research":"research","analyst":"analyst","writer":"writer",END:END})
    wf.add_edge("research","supervisor")
    wf.add_edge("analyst","supervisor")
    wf.add_edge("writer","supervisor")
    return wf.compile()

app = build()
RD = Path(__file__).parent/"reports"

def _save(topic, report, rd, ana):
    RD.mkdir(parents=True,exist_ok=True)
    s = re.sub(r'[\\/:*?"<>|]','',topic)
    s = re.sub(r'\s+','_',s.strip())[:50] or "report"
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    p = f"{s}_{ts}"
    (RD/f"{p}_报告.md").write_text(report,encoding="utf-8")
    (RD/f"{p}_原始资料.md").write_text("\n".join(f"## 资料 {i+1}\n\n{d}" for i,d in enumerate(rd)),encoding="utf-8")
    (RD/f"{p}_分析摘要.md").write_text(f"# {topic}\n\n{ana.get('llm_analysis','')}",encoding="utf-8")

def run(topic):
    print(f"🚀 {topic}")
    r,rd,a = "",[],{}
    for ch in app.stream(ResearchState(topic=topic)):
        for n,u in ch.items():
            print(f"  {n}完成")
            if "raw_data" in u: rd=u["raw_data"]
            if "analysis" in u: a=u["analysis"]
            if n=="writer": r=u.get("final_report","")
    print("✅ 完成")
    return r,rd,a

if __name__=="__main__":
    t = input("主题: ").strip() or "2026年新能源汽车出海趋势"
    r,rd,a = run(t)
    _save(t,r,rd,a)
