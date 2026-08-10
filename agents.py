import json, os
from typing import Dict, List, Optional
from langgraph.graph import END
from state import ResearchState
from prompts import SUPERVISOR_PROMPT, RESEARCHER_PROMPT, ANALYST_PROMPT, WRITER_PROMPT

def _build_chain(sp, temp=0.7, timeout=60, mt=4096):
    k = os.getenv("DEEPSEEK_API_KEY","")
    if not k or k.startswith("sk-your-"): return None
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        llm = ChatOpenAI(model=os.getenv("DEEPSEEK_MODEL","deepseek-v4-flash"),api_key=k,
            base_url=os.getenv("DEEPSEEK_API_BASE","https://api.deepseek.com"),
            temperature=temp,request_timeout=timeout,max_retries=2,max_tokens=mt)
        return ChatPromptTemplate.from_messages([("system",sp),("human","{input}")])|llm
    except: return None

c_super = _build_chain(SUPERVISOR_PROMPT,0)
c_res = _build_chain(RESEARCHER_PROMPT,0.7)
c_ana = _build_chain(ANALYST_PROMPT,0.3,180,8192)
c_wr = _build_chain(WRITER_PROMPT,0.7,300,8192)

def _build_search():
    k = os.getenv("TAVILY_API_KEY","")
    if not k or k.startswith("tvly-your-"): return None
    try:
        from langchain_tavily import TavilySearch
        return TavilySearch(max_results=5,topic="general",include_answer=True)
    except: return None

search = _build_search()

def _build_res_llm():
    k = os.getenv("DEEPSEEK_API_KEY","")
    if not k or k.startswith("sk-your-") or not search: return None
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=os.getenv("DEEPSEEK_MODEL","deepseek-v4-flash"),api_key=k,
            base_url=os.getenv("DEEPSEEK_API_BASE","https://api.deepseek.com"),
            temperature=0.7,request_timeout=90,max_retries=3)
        return llm.bind_tools([search])
    except: return None

res_llm = _build_res_llm()
cb: Optional = None

def _invoke(chain, inp):
    if not chain: return ""
    try: return chain.invoke({"input":inp}).content
    except: return ""

def _run_react(topic):
    if not res_llm: return None
    from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
    msgs = [SystemMessage(content=RESEARCHER_PROMPT), HumanMessage(content=topic)]
    for i in range(5):
        if cb: cb("iter_start","")
        r = None
        for a in range(3):
            try: r = res_llm.invoke(msgs); break
            except Exception as e:
                if a<2: import time;time.sleep(2*(a+1))
                else: return None
        if not r: return None
        msgs.append(r)
        tcs = getattr(r,"tool_calls",None)
        if not tcs:
            if cb: cb("done","")
            return [r.content.strip()] if r.content else []
        for tc in tcs[:3]:
            args = tc.get("args",{}) if isinstance(tc,dict) else getattr(tc,"args",{})
            tid = tc.get("id","") if isinstance(tc,dict) else getattr(tc,"id","")
            if cb: cb("search",args.get("query",""))
            try:
                res = search.invoke(args)
                try: rs = json.dumps(res,ensure_ascii=False) if isinstance(res,dict) else str(res)
                except: rs = str(res)
                msgs.append(ToolMessage(content=rs,tool_call_id=tid))
            except Exception as e:
                msgs.append(ToolMessage(content=str(e),tool_call_id=tid))
    msgs.append(HumanMessage(content="整理输出"))
    return [res_llm.invoke(msgs).content.strip()]

def supervisor(state):
    r = _invoke(c_super,f"主题:{state.topic} 资料:{len(state.raw_data)} 分析:{bool(state.analysis)} 报告:{bool(state.final_report)}")
    if r:
        t = r.lower()
        if "finish" in t: return END
        if "research" in t: return "research"
        if "analyst" in t: return "analyst"
        if "writer" in t: return "writer"
    if not state.raw_data: return "research"
    if not state.analysis: return "analyst"
    if not state.final_report: return "writer"
    return END

def route_after(state):
    return state.next_agent if state.next_agent in ("research","analyst","writer",END) else "research"

def research(state):
    t = state.topic
    if res_llm:
        try:
            d = _run_react(t)
            if d: return {"raw_data":state.raw_data+d,"next_agent":"analyst"}
        except: pass
    if search:
        dims = [("市场规模",f"{t} 市场规模 2025"),("竞争格局",f"{t} 竞争格局"),
                ("政策",f"{t} 政策 2025"),("技术",f"{t} 技术趋势"),("需求",f"{t} 用户需求")]
        new = []
        for n,q in dims:
            try:
                r = search.invoke({"query":q})
                if isinstance(r,dict):
                    its = []
                    if r.get("answer"): its.append(r["answer"])
                    for item in r.get("results",[]):
                        c = item.get("content") or item.get("raw_content") or ""
                        if c: its.append(f"{item.get('title','')}:{c[:200]}")
                    if its: new.append(f"【{n}】"+" | ".join(its))
            except: pass
        if new: return {"raw_data":state.raw_data+new,"next_agent":"analyst"}
    r = _invoke(c_res,f"搜集{t}行业资料")
    d = [x.strip() for x in r.split("\n") if x.strip()] if r else [f"{t}资料需配置API Key"]
    return {"raw_data":state.raw_data+d,"next_agent":"analyst"}

def analyst(state):
    raw = "\n".join(state.raw_data)
    r = _invoke(c_ana,f"分析以下资料：\n\n{raw}")
    a = {"topic":state.topic,"llm_analysis":r,"raw_summary":raw} if r else {"topic":state.topic,"llm_analysis":"","error":"LLM不可用"}
    return {"analysis":a,"next_agent":"writer"}

def writer(state):
    a = state.analysis or {}
    t = state.topic or ""
    at = a.get("llm_analysis","")
    rt = "\n".join(state.raw_data)
    inp = f"主题:{t}\n分析:{at}\n资料:{rt[:30000]}\n撰写3000-5000字行业调研报告"
    r = _invoke(c_wr,inp)
    rep = r if r else f"# {t}调研报告\n\nLLM不可用，请配置API Key"
    return {"final_report":rep,"next_agent":END}
