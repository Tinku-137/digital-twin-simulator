# server.py
"""
FastAPI server for Digital Twin demo.
Endpoints:
  POST /update   -> receive JSON payload from ESP32: {"temp":..,"vibration":..,"sound":..,"current":..}
  GET  /latest   -> return last received reading (JSON)
  GET  /health   -> simple health check
"""

import time
import csv
import os
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

LOG_CSV = "sensor_log.csv"

app = FastAPI(title="Digital Twin FastAPI")

# Allow CORS from everywhere for easy testing (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory storage of latest reading
latest_data = {
    "temp": None,
    "vibration": None,
    "sound": None,
    "current": None,
    "current_amps": None,
    "ts": None
}

# Pydantic model for request validation
class SensorPayload(BaseModel):
    temp: float
    vibration: float
    sound: float
    current: float  # numeric value that may be an ADC-scaled or already amps

def calculate_current_amps(curr_raw: float) -> Optional[float]:
    """
    Convert the incoming 'current' value to amps if needed.
    Heuristic from previous notes:
      - If curr_raw <= 50 treat as already measured amps (or small raw)
      - Else treat it as scaled value: curr_raw = ADC_val * SCALE (SCALE=0.04)
        and convert back to ADC and compute amps assuming ACS712-like sensor.
    This function is defensive and returns None if conversion fails.
    """
    try:
        if curr_raw is None:
            return None
        curr_raw = float(curr_raw)
        # If value is small, assume it's already amps
        if curr_raw <= 50:
            return round(abs(curr_raw), 3)
        # Else try to convert back to an ADC reading and compute approximate amps
        SCALE = 0.04  # used on ESP32 before sending (raw * 0.04)
        adc_val = curr_raw / SCALE
        adc_max = 4095.0
        Vref = 3.3
        voltage = (adc_val / adc_max) * Vref
        v_zero = Vref / 2.0
        sensitivity = 0.185  # typical ACS712 5A variant sensitivity (V/A) — adjust if different
        amps = (voltage - v_zero) / sensitivity
        amps = abs(amps)
        if amps != amps:  # NaN check
            return None
        return round(amps, 3)
    except Exception:
        return None

def append_csv_row(row: dict):
    header = ["ts", "temp", "vibration", "sound", "current", "current_amps"]
    first = not os.path.exists(LOG_CSV)
    try:
        with open(LOG_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            if first:
                writer.writerow(header)
            writer.writerow([row.get("ts"), row.get("temp"), row.get("vibration"),
                             row.get("sound"), row.get("current"), row.get("current_amps")])
    except Exception as e:
        # Do not break the API if logging fails; just print a message
        print("Warning: failed to append CSV row:", e)

@app.post("/update")
async def update_sensor(request: Request):
    """
    Receive sensor POST from ESP32 or other clients.
    Expects JSON matching SensorPayload.
    """
    global latest_data

    client_ip = request.client.host if request.client else "unknown"
    try:
        payload = await request.json()
    except Exception as e:
        print(f"Bad JSON from {client_ip}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Log raw payload for debugging
    print(f"RECEIVED POST from {client_ip} -> {payload}")

    # Validate using Pydantic model
    try:
        validated = SensorPayload(**payload)
    except Exception as e:
        print(f"Validation error from {client_ip}: {e}")
        raise HTTPException(status_code=422, detail="Payload validation failed")

    ts = time.time()
    current_amps = calculate_current_amps(validated.current)

    latest_data = {
        "temp": round(float(validated.temp), 3),
        "vibration": round(float(validated.vibration), 3),
        "sound": round(float(validated.sound), 3),
        "current": round(float(validated.current), 3),
        "current_amps": current_amps,
        "ts": ts
    }

    # Append to CSV (best-effort)
    append_csv_row(latest_data)

    return {"status": "ok", "received_at": ts}

@app.get("/latest")
async def get_latest():
    """Return the latest reading as JSON. If none seen yet, returns 204 No Content."""
    if latest_data["ts"] is None:
        return {}  # or you can raise HTTPException(status_code=204)
    return latest_data

@app.get("/health")
async def health():
    return {"status": "running", "ts": time.time()}

if __name__ == "__main__":
    import uvicorn
    print("Starting uvicorn server on 0.0.0.0:5000")
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
