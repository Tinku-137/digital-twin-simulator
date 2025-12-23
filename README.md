# AI-Driven Digital Twin Simulator

This project implements an AIoT-based Digital Twin Simulator for real-time machine monitoring and predictive analysis.

## Features
- Real-time sensor data acquisition using ESP32
- Sensors: Temperature (DS18B20), Vibration, Sound, Current
- FastAPI backend for data ingestion
- Streamlit dashboard for visualization
- Performance scoring and AI insights
- Predictive maintenance concept

## Tech Stack
- ESP32
- Python
- FastAPI
- Streamlit
- Plotly
- GitHub

## How to Run
1. Start FastAPI server:

uvicorn server:app --reload --host 0.0.0.0 --port 5000

2. Start Streamlit dashboard:
streamlit run app.py

markdown
Copy code
3. Power ESP32 (ensure same WiFi network)

## Author
Praveen Kumar
