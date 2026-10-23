# CAN Bus Diagnostics Dashboard

Screenshot-inspired dashboard prototype based on the supplied CAN diagnostics mockup and the Mark_23_hybrid notebook.

## Features
- Dark navy, cyan, green and yellow diagnostics UI
- FastAPI backend at `/api/status` and `/api/health`
- Refreshing simulated RPM, coolant-temperature and system-voltage telemetry
- Responsive layout

> **Important:** Data is simulated. This repository is not connected to live CAN hardware; integrate a real adapter and the model from the notebook before relying on it for vehicle diagnostics.

## Run locally
Python 3.10+

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

## Project files
- `app/main.py` — FastAPI backend and telemetry API
- `app/static/` — dashboard frontend
- `notebooks/Mark_23_hybrid.ipynb` — original project notebook (to be uploaded separately if needed)
