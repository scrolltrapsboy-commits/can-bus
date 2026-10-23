from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import random, time, math
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
app = FastAPI(title="CAN Bus Diagnostics API", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
started = time.time()

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/status")
def status():
    t = time.time()
    rpm = round(2493 + 170 * math.sin(t / 8) + random.uniform(-22, 22))
    temp = round(88.4 + 1.7 * math.sin(t / 14) + random.uniform(-0.25, 0.25), 1)
    volt = round(13.91 + 0.12 * math.sin(t / 11) + random.uniform(-0.025, 0.025), 2)
    state = "Critical" if temp >= 95 or rpm >= 3900 else ("Warning" if temp >= 92 or volt < 13.2 else "Normal")
    return {
        "service": "CAN Bus Diagnostics API",
        "simulator": "active",
        "frequency_hz": 100,
        "engine_rpm": rpm,
        "coolant_temp_c": temp,
        "system_voltage_v": volt,
        "operational_state": state,
        "uptime_seconds": int(t - started),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_status": "Training pipeline currently in progress",
        "source": "simulated telemetry",
    }

@app.get("/api/health")
def health():
    return {"ok": True, "service": "can-bus-diagnostics"}
