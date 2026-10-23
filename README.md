# CAN Bus Diagnostics — Project 18

A larger screenshot-inspired dashboard and runnable API for the **notebook-derived CAN simulation and predictive failure detection workflow**.

## What Start Pipeline runs

The **START PIPELINE** button calls `POST /api/run` and executes `app/pipeline.py`, adapted from the uploaded `Mark_23_hybrid.ipynb` algorithm:

1. Generate virtual CAN frames for four IDs (`0x100`–`0x103`) across NORMAL, EARLY_DEGRADATION, and SEVERE_ABNORMALITY scenarios.
2. Clean and validate timestamps, CAN IDs and 8-byte payloads; extract payload bytes and inter-arrival timing.
3. Build 5-second windows and the notebook's traffic, timing and payload features.
4. Train a 300-tree Isolation Forest on NORMAL windows, calculate 95th/99th percentile thresholds and classify NORMAL/WARNING/CRITICAL.
5. Display generated frame/window counts, anomaly scores, alert distribution, weighted precision/recall/F1, false-positive/false-negative rates and recent predictions.

The dashboard polls the API for progress and execution logs. Generated files are written to `outputs/`.

## Run locally (Python 3.10+)

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Interactive API docs: http://127.0.0.1:8000/docs

## Render

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Root directory:** leave blank

## Endpoints

- `GET /` — dashboard
- `GET /api/health` — service health
- `GET /api/status` — current pipeline state
- `POST /api/run` — start the notebook-derived run
- `GET /api/results` — progress, logs, summary, telemetry and recent predictions

## Important data note

The notebook itself generates **simulated virtual CAN data**; this is not live vehicle telemetry. The dashboard shows results from the simulation and Isolation Forest run, not pre-filled demo numbers or a physical car connection.
