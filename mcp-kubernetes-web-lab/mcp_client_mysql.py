import json
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

app = FastAPI()
MCP_URL = os.getenv("MCP_URL", "http://mcp-server:8000/mcp")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama.default.svc.cluster.local:11434/api/chat")
MODEL = os.getenv("MODEL", "gemma3:12b")

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

async def ollama(prompt, json_mode=False):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False}
    if json_mode:
        body["format"] = "json"
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(OLLAMA_URL, json=body)
        response.raise_for_status()
        return response.json()["message"]["content"]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ERP Product Assistant</title><style>body{font:16px Arial;max-width:760px;margin:50px auto;padding:0 20px;color:#222}textarea{width:100%;box-sizing:border-box;padding:12px;font:inherit}button{padding:10px 20px;margin:12px 0;cursor:pointer}pre{white-space:pre-wrap;background:#f5f5f5;padding:16px;min-height:3em}small{color:#555}</style></head><body><h1>ERP Product Assistant</h1><p>Ask about a product using its product code.</p><form id="form"><textarea id="q" rows="3" required placeholder="What is the stock of B200?"></textarea><button id="send">Ask</button></form><h3>Answer</h3><pre id="answer">Waiting for a question.</pre><details><summary>Tool result</summary><pre id="debug"></pre></details><script>const f=document.getElementById('form'),a=document.getElementById('answer'),d=document.getElementById('debug'),b=document.getElementById('send');f.onsubmit=async(e)=>{e.preventDefault();b.disabled=true;a.textContent='Processing...';d.textContent='';try{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.getElementById('q').value})});const x=await r.json();if(!r.ok)throw new Error(x.detail||'Request failed');a.textContent=x.answer;d.textContent=JSON.stringify(x.tool_result,null,2)}catch(err){a.textContent='Error: '+err.message}finally{b.disabled=false}};</script></body></html>"""

@app.post("/ask")
async def ask(data: Question):
    question = data.question.strip()
    if not question:
        raise HTTPException(400, "Enter a question.")
    prompt = f"""You are an ERP assistant. The available tool is get_product_stock(product_code), which requires an exact product code. Extract a code only when it is explicitly present in the user's question. Never guess or invent a code. Return JSON only: {{"tool":"get_product_stock","arguments":{{"product_code":"B200"}}}} or, if no product code is present, {{"tool":null}}. User question: {question}"""
    try:
        decision = json.loads(await ollama(prompt, json_mode=True))
        if decision.get("tool") is None:
            return {"answer": "Please provide a product code, for example B200.", "tool_result": None}
        if decision.get("tool") != "get_product_stock":
            raise ValueError("The model selected an unsupported tool.")
        code = decision.get("arguments", {}).get("product_code")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("The model did not provide a product code.")
        async with streamablehttp_client(MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("get_product_stock", arguments={"product_code": code.strip()})
                text = "\n".join(item.text for item in result.content if hasattr(item, "text"))
                if result.isError:
                    raise RuntimeError("MCP tool error: " + text)
        final = await ollama(f"Answer the question in English using only the ERP result. If not found, say so. Do not invent facts.\nQuestion: {question}\nERP result: {text}")
        try:
            tool_result = json.loads(text)
        except json.JSONDecodeError:
            tool_result = text
        return {"answer": final, "tool_result": tool_result}
    except (httpx.HTTPError, ValueError, KeyError, RuntimeError) as exc:
        raise HTTPException(502, f"Service error: {exc}") from exc
