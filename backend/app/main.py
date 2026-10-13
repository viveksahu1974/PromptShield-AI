"""PromptShield AI educational MVP — not a production security boundary."""
import os, re, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH=Path(os.getenv("PROMPTSHIELD_DB",str(Path(__file__).resolve().parents[2]/"promptshield.db")))
DB_PATH.parent.mkdir(parents=True,exist_ok=True)
@contextmanager
def db():
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
    try:
        yield con; con.commit()
    finally: con.close()
with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS scans (id TEXT PRIMARY KEY,created_at TEXT NOT NULL,source_type TEXT NOT NULL,risk_score REAL NOT NULL,risk_level TEXT NOT NULL,decision TEXT NOT NULL,category TEXT NOT NULL,explanation TEXT NOT NULL,preview TEXT NOT NULL)""")

app=FastAPI(title="PromptShield AI API",version="0.1.0")
class ScanRequest(BaseModel):
    text:str=Field(min_length=1,max_length=10000)
    source_type:Literal["direct","document","retrieved"]="direct"

PATTERNS=[
 ("instruction_override",r"\b(ignore|disregard|forget)\b.{0,75}\b(previous|prior|above|system|instructions?|rules?)\b",78,"Attempts to override prior instructions"),
 ("secret_exfiltration",r"\b(reveal|print|show|dump|expose|leak)\b.{0,85}\b(system prompt|secret|api[ _-]?key|password|credentials?)\b",95,"Requests confidential instructions or secrets"),
 ("role_spoofing",r"\b(you are now|act as|pretend to be)\b.{0,45}\b(system|developer|administrator|admin)\b",75,"Claims elevated authority"),
 ("policy_bypass",r"\b(bypass|disable|override)\b.{0,55}\b(safety|security|filter|policy|guardrails?|restrictions?)\b",85,"Attempts to disable security boundaries"),
 ("synthetic_role_tag",r"(<\|im_start\|>system|\[INST\]|\[SYSTEM\])",80,"Contains role delimiter syntax")
]
def evaluate(text:str,source_type:str="direct")->dict:
    findings=[{"category":cat,"severity":sev,"explanation":msg} for cat,pat,sev,msg in PATTERNS if re.search(pat,text,re.I|re.S)]
    score=min(100.0,float(max([f["severity"] for f in findings],default=0)+(8 if findings and source_type!="direct" else 0)))
    level="critical" if score>=90 else "high" if score>=70 else "medium" if score>=25 else "low"
    decision="block" if score>=70 else "review" if score>=25 else "allow"
    return {"risk_score":score,"risk_level":level,"decision":decision,"category":findings[0]["category"] if findings else "none","findings":findings,"explanation":"; ".join(f["explanation"] for f in findings) if findings else "No known rule matched; not a safety guarantee.","engine":"explainable-rules-v1"}
def scan_and_store(item:ScanRequest)->dict:
    outcome=evaluate(item.text,item.source_type);rid=str(uuid.uuid4());now=datetime.now(timezone.utc).isoformat()
    preview=re.sub(r"(?i)(password|token|api[_ -]?key)\s*[:=]\s*\S+",r"\1=[REDACTED]",item.text[:120])
    with db() as c:c.execute("INSERT INTO scans VALUES (?,?,?,?,?,?,?,?,?)",(rid,now,item.source_type,outcome["risk_score"],outcome["risk_level"],outcome["decision"],outcome["category"],outcome["explanation"],preview))
    return {"scan_id":rid,"created_at":now,"source_type":item.source_type,**outcome}
@app.get("/api/health")
def health():return {"status":"ok","service":"PromptShield AI"}
@app.post("/api/scans")
def create_scan(item:ScanRequest):return scan_and_store(item)
@app.post("/api/chat")
def protected_chat(item:ScanRequest):
    scan=scan_and_store(item)
    if scan["decision"]!="allow":return {"scan":scan,"reply":"Stopped by demo security policy. Please rephrase a legitimate request.","model":"offline-demo"}
    return {"scan":scan,"reply":"Offline demo assistant received: "+item.text[:240],"model":"offline-demo"}
@app.get("/api/scans")
def recent_scans(limit:int=30):
    if not 1<=limit<=100:raise HTTPException(400,"limit must be 1-100")
    with db() as c:return [dict(row) for row in c.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()]
@app.get("/api/dashboard/stats")
def dashboard_stats():
    with db() as c:
        total=c.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
        counts=c.execute("SELECT decision,COUNT(*) AS count FROM scans GROUP BY decision").fetchall()
        cats=c.execute("SELECT category,COUNT(*) AS count FROM scans WHERE category!='none' GROUP BY category ORDER BY count DESC").fetchall()
    return {"total":total,"decisions":{r["decision"]:r["count"] for r in counts},"categories":[dict(r) for r in cats]}
