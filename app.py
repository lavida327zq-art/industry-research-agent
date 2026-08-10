import io,threading,time,zipfile
from pathlib import Path
from dotenv import load_dotenv
_ENV = Path(__file__).parent/".env"
if _ENV.exists(): load_dotenv(_ENV)
import streamlit as st
import agents
from state import ResearchState
from main import app, _save

st.set_page_config(page_title="智能行业调研助手",page_icon="📊",layout="wide")
if "_s" not in st.session_state:
    st.session_state._s = {"running":False,"logs":[],"rmsgs":[],"pct":0.0,"stage":"","detail":"","report":"","raw":[],"ana":{},"err":"","step":0}
if "_l" not in st.session_state: st.session_state._l = threading.Lock()
_s=st.session_state._s; _l=st.session_state._l

def _reset():
    with _l: _s.clear(); _s.update({"running":True,"logs":[],"rmsgs":[],"pct":0.0,"stage":"","detail":"","report":"","raw":[],"ana":{},"err":"","step":0})

def _cb(e,m):
    with _l:
        if e=="iter_start": _s["rmsgs"].append("🤔 搜索中...")
        elif e=="search": _s["rmsgs"].append(f"🔍 {m}")
        elif e=="done": _s["rmsgs"].append(f"✅ {m}")

def _run(topic):
    try:
        agents.cb = _cb
        for ch in app.stream(ResearchState(topic=topic)):
            for n,u in ch.items():
                with _l: _s["step"]+=1
                stage={"supervisor":"🧠 智能调度","research":"🔍 搜集资料","analyst":"📊 分析洞察","writer":"✍️ 撰写报告"}.get(n,n)
                with _l:
                    _s["stage"]=stage;_s["logs"].append(f"✅ {stage}")
                    if "raw_data" in u: _s["raw"]=u["raw_data"]
                    if "analysis" in u: _s["ana"]=u["analysis"]
                    if n=="writer": _s["report"]=u.get("final_report","")
        with _l: r=_s["report"];rd=_s["raw"];a=_s["ana"]
        if r: _save(topic,r,rd,a)
        with _l: _s["pct"]=1.0;_s["running"]=False
        agents.cb=None
    except Exception as e:
        with _l: _s["err"]=str(e);_s["running"]=False

with st.sidebar:
    st.title("🎯 开始调研")
    topic=st.text_input("主题",value="",placeholder="请输入调研主题",label_visibility="collapsed")
    running=_s.get("running",False)
    btn=st.button("🚀 开始调研",type="primary",use_container_width=True,disabled=running)
    st.markdown("💡 AI自动完成全流程")

st.title("📊 智能行业调研助手")
if btn and topic.strip():
    _reset()
    threading.Thread(target=_run,args=(topic.strip(),),daemon=True).start()
    st.rerun()
if _s.get("running"):
    pct=_s.get("pct",0.0);stage=_s.get("stage","")
    st.progress(pct,text=f"{stage}")
    with st.status("🔄 实时动态",expanded=True) as s:
        for l in _s.get("logs",[]): st.markdown(l)
        for m in _s.get("rmsgs",[]): st.markdown(m)
        s.update(state="complete")
    time.sleep(1);st.rerun()
if _s.get("report"):
    st.subheader("✅ 调研完成")
    r=_s["report"];tv=topic.strip() or "调研报告"
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as zf: zf.writestr(f"{tv}.md",r)
    buf.seek(0)
    st.download_button("📦 下载报告",buf,file_name=f"{tv}.zip",mime="application/zip",type="primary")
    st.markdown(r)
