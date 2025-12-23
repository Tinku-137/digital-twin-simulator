import streamlit as st
import random
import time

st.set_page_config(page_title="Digital Twin Simulator", layout="wide")

st.title("🧠 AI-Based Digital Twin Simulator Dashboard")
st.markdown("Simulating machine condition using 4 sensors: **Vibration**, **Acoustic**, **Temperature**, and **Current**")

# --- Threshold limits ---
VIBRATION_LIMIT = 0.6       # g
ACOUSTIC_LIMIT = 2.5        # Pascal
TEMPERATURE_LIMIT = 65       # Celsius
CURRENT_LIMIT = 7.5          # Ampere

# --- Layout setup ---
col1, col2, col3, col4 = st.columns(4)

placeholder = st.empty()

# --- Main Simulation Loop ---
while True:
    # Simulate sensor readings
    vibration = round(random.uniform(0.1, 1.0), 2)
    acoustic = round(random.uniform(0.5, 4.0), 2)
    temperature = round(random.uniform(30, 90), 1)
    current = round(random.uniform(3.0, 9.0), 2)

    # --- Determine condition ---
    status = "Normal"
    if (vibration > VIBRATION_LIMIT or
        acoustic > ACOUSTIC_LIMIT or
        temperature > TEMPERATURE_LIMIT or
        current > CURRENT_LIMIT):
        status = "Faulty"

    # --- Update dashboard ---
    with placeholder.container():
        st.subheader("🔹 Live Sensor Readings")

        col1.metric("Vibration (g)", vibration, delta=None)
        col2.metric("Acoustic (Pa)", acoustic, delta=None)
        col3.metric("Temperature (°C)", temperature, delta=None)
        col4.metric("Current (A)", current, delta=None)

        st.markdown("---")
        if status == "Normal":
            st.success("✅ Machine Health Status: NORMAL")
        else:
            st.error("⚠️ Machine Health Status: FAULT DETECTED")

        st.progress(min((vibration / VIBRATION_LIMIT), 1.0))
        st.progress(min((acoustic / ACOUSTIC_LIMIT), 1.0))
        st.progress(min((temperature / TEMPERATURE_LIMIT), 1.0))
        st.progress(min((current / CURRENT_LIMIT), 1.0))

        st.markdown("Refreshes every second for simulation...")
        
    time.sleep(1)
