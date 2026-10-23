# CAN Bus Diagnostics Dashboard

A runnable dashboard prototype based on the uploaded `Mark_23_hybrid.ipynb` notebook and supplied reference screenshot.

## Features
- Screenshot-matched dark diagnostic panel, status indicator, three architecture cards, telemetry metrics, operational state indicators and footer.
- FastAPI endpoints: `/api/health` and `/api/status`.
- Live simulated RPM, coolant temperature and system voltage refresh every 1.5 seconds.
- Responsive layout for smaller screens.
- Original notebook preserved under `notebooks/`.

> **Important:** The dashboard currently displays generated/simulated telemetry. It does not connect to a physical CAN adapter or claim a trained production classifier. Integrate your real CAN interface and trained model before using it for vehicle decisions.

## Run locally (Python 3.10+)
```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

## Repository contents
- `app/main.py` — FastAPI service and simulated telemetry API
- `app/static/` — frontend
- `notebooks/Mark_23_hybrid.ipynb` — original uploaded notebook
- `assets/reference-dashboard.png` — supplied dashboard reference
