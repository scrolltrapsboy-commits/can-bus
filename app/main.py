from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import threading, time
from app import pipeline

BASE=Path(__file__).resolve().parent
app=FastAPI(title="CAN Bus Diagnostics API",version="2.0.0")
app.mount("/static",StaticFiles(directory=BASE/"static"),name="static")

@app.get("/")
def home(): return FileResponse(BASE/"static"/"index.html")

@app.get("/api/health")
def health(): return {"ok":True,"service":"can-bus-diagnostics"}

@app.get("/api/status")
def status():
    state=pipeline.snapshot()
    return {"service":"CAN Bus Diagnostics API","simulator":"active" if state["status"] in ("running","completed") else "ready",
            "frequency_hz":100,"pipeline":state}

@app.post("/api/run")
def run_pipeline():
    state=pipeline.snapshot()
    if state["status"]=="running": return {"ok":True,"message":"Pipeline is already running","pipeline":state}
    threading.Thread(target=pipeline.run_pipeline,daemon=True).start()
    return {"ok":True,"message":"Notebook pipeline started"}

@app.get("/api/results")
def results():
    state=pipeline.snapshot()
    return {"status":state["status"],"summary":state["summary"],"telemetry":state["telemetry"],
            "results":state["results"],"logs":state["logs"],"error":state["error"],
            "progress":state["progress"],"stage":state["stage"]}
