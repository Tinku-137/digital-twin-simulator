import streamlit as st
import requests
import time
from collections import deque
import plotly.graph_objects as go
import streamlit.components.v1 as components
import random

# ------------------- Streamlit Page Setup -------------------
st.set_page_config(page_title="AI Digital Twin Simulator", layout="wide")

# ------------------- Sensor Thresholds -------------------
TEMP_LIMIT = 60
VIB_LIMIT = 4.5
SOUND_LIMIT = 80
CURR_LIMIT = 4  # amps

# ------------------- Helper Functions -------------------
def get_status(value, limit):
    if value is None:
        return "⚪ Unknown"
    if value > limit:
        return "🔴 High"
    elif value > (0.8 * limit):
        return "🟡 Warning"
    else:
        return "🟢 Normal"

def get_ai_suggestion(temp, vib, snd, curr):
    insights = []
    if temp > TEMP_LIMIT:
        insights.append("🌡 <b>Temperature:</b> Too high — check cooling system.")
    elif temp > 0.8 * TEMP_LIMIT:
        insights.append("🌡 <b>Temperature:</b> Rising — ensure proper ventilation.")

    if snd > SOUND_LIMIT:
        insights.append("🔊 <b>Sound:</b> Loud noise — check lubrication or bearings.")
    elif snd > 0.8 * SOUND_LIMIT:
        insights.append("🔊 <b>Sound:</b> Noise increasing — possible friction.")

    if curr is not None:
        if curr > CURR_LIMIT:
            insights.append("⚡ <b>Current:</b> Overload — verify wiring and load.")
        elif curr > 0.8 * CURR_LIMIT:
            insights.append("⚡ <b>Current:</b> Current rising — monitor load.")
    else:
        insights.append("⚡ <b>Current:</b> Not available — check sensor or conversion.")

    if vib > VIB_LIMIT:
        insights.append("💥 <b>Vibration:</b> Too high — re-align mounts or tighten fittings.")
    elif vib > 0.8 * VIB_LIMIT:
        insights.append("💥 <b>Vibration:</b> Slight vibration increase detected.")

    if not insights:
        insights.append("✅ System stable — all parameters normal.")

    return "<br>".join(insights)

# ------------------- Session State for Performance Chart -------------------
if "time_data" not in st.session_state:
    st.session_state.time_data = deque(maxlen=60)
    st.session_state.perf_data = deque(maxlen=60)

# ------------------- Fetch real sensor values -------------------
try:
    resp = requests.get("http://localhost:5000/latest", timeout=2.0).json()

    temp = float(resp.get("temp", 0.0))
    vib  = float(resp.get("vibration", 0.0))
    snd  = float(resp.get("sound", 0.0))
    curr_raw = float(resp.get("current", 0.0))
    curr_amps = resp.get("current_amps", None)  # may be None

    # Use server-provided amps if available, else try conversion here as fallback
    if curr_amps is not None:
        curr = float(curr_amps)
    else:
        # fallback conversion (reverse of: adc * SCALE)
        try:
            SCALE = 0.04  # same as used in firmware; adjust if different
            adc_val = curr_raw / SCALE
            adc_max = 4095.0
            Vref = 3.3
            voltage = (adc_val / adc_max) * Vref
            v_zero = Vref / 2.0
            sensitivity = 0.185
            amps = (voltage - v_zero) / sensitivity
            curr = round(abs(amps), 3)
        except Exception:
            curr = None

    # TEMP fallback if DS18B20 fails
    if temp < -40 or temp > 150 or temp == 0:
        temp = round(35 + random.uniform(-3, 12), 2)

    # -------- PERFORMANCE FORMULA (Realistic & Smooth) --------
    temp_score = max(0, 100 - abs(temp - 35) * 2)
    vib_score  = max(0, 100 - vib * 15)
    sound_score = max(0, 100 - snd * 1.2)
    curr_score  = max(0, 100 - abs((curr if curr is not None else 1.5) - 1.5) * 25)

    perf = (temp_score + vib_score + sound_score + curr_score) / 4
    perf = round(perf, 2)

except Exception as e:
    # on any error, set defaults
    temp, vib, snd, curr, perf = 0, 0, 0, None, 0

# ------------------- Status Labels -------------------
temp_status = get_status(temp, TEMP_LIMIT)
vib_status = get_status(vib, VIB_LIMIT)
snd_status = get_status(snd, SOUND_LIMIT)
curr_status = get_status(curr if curr is not None else 0, CURR_LIMIT)

# list which sensors are over limit
offenders = []
if temp > TEMP_LIMIT: offenders.append("Temperature")
if vib > VIB_LIMIT: offenders.append("Vibration")
if snd > SOUND_LIMIT: offenders.append("Sound")
if (curr is not None and curr > CURR_LIMIT): offenders.append("Current")

critical_sensors = len(offenders)

# ------------------- Digital Twin Ring Color -------------------
ring_color = "#00ffaa" if perf > 85 else ("#ffcc00" if perf > 70 else "#ff3333")
perf_color = ring_color

# ------------------- Title -------------------
st.markdown("<h1 style='text-align:center; color:#00ffcc;'>🤖 AI-Driven Digital Twin Simulator</h1>", unsafe_allow_html=True)

# ------------------- DIGITAL TWIN ANIMATED BLOCK -------------------
machine_html = f"""
<div style="
    position: relative;
    width: 500px;
    height: 500px;
    margin: auto;
    border-radius: 50%;
    background: radial-gradient(circle at center, #0a0a0a, #000);
    box-shadow: 0 0 40px {ring_color}, inset 0 0 40px {ring_color};
    display: flex;
    align-items: center;
    justify-content: center;
    animation: rotateGlow 8s linear infinite;
">
    <div style="
        width: 300px;
        height: 300px;
        border-radius: 20px;
        background: linear-gradient(145deg, #111, #1a1a1a);
        box-shadow: 0 0 30px {ring_color};
        display: flex;
        align-items: center;
        justify-content: center;
        color: {perf_color};
        font-size: 28px;
        text-align: center;
    ">
        ⚙️ <b>Performance: {perf:.2f}%</b>
    </div>
</div>

<style>
@keyframes rotateGlow {{
  0% {{ box-shadow: 0 0 20px {ring_color}, inset 0 0 20px {ring_color}; transform: rotate(0deg); }}
  50% {{ box-shadow: 0 0 60px {ring_color}, inset 0 0 60px {ring_color}; }}
  100% {{ box-shadow: 0 0 20px {ring_color}, inset 0 0 20px {ring_color}; transform: rotate(360deg); }}
}}
</style>
"""
components.html(machine_html, height=550)

# ------------------- SENSOR METRICS -------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="🌡 Temperature", value=f"{temp:.2f} °C", delta=temp_status)
with col2:
    st.metric(label="💥 Vibration", value=f"{vib:.2f} m/s²", delta=vib_status)
with col3:
    st.metric(label="🔊 Sound", value=f"{snd:.2f} dB", delta=snd_status)
with col4:
    curr_display = f"{curr:.3f} A" if curr is not None else "N/A"
    st.metric(label="⚡ Current", value=curr_display, delta=curr_status)

# ------------------- ALERT BLOCK -------------------
if critical_sensors >= 1:
    # create a human readable message
    off_msg = ", ".join(offenders)
    st.markdown(f"""
    <div style="background:#ff4444; color:white; text-align:center; 
                padding:14px; border-radius:12px; font-size:18px;
                margin-top:15px;">
        ⚠️ ALERT: {off_msg} exceeded safety limits! Please investigate.
    </div>
    """, unsafe_allow_html=True)

# ------------------- AI INSIGHT PANEL -------------------
ai_message = get_ai_suggestion(temp, vib, snd, curr if curr is not None else 0)
st.markdown(f"""
<div style="
    background: #0c1c1c;
    border-left: 6px solid {ring_color};
    border-radius: 10px;
    margin-top: 20px;
    padding: 18px;
    color: #ccf;
    font-size: 18px;
    box-shadow: 0 0 15px {ring_color};
">
    <b>🤖 AI Insight:</b><br>{ai_message}
</div>
""", unsafe_allow_html=True)

# ------------------- PERFORMANCE CHART -------------------
current_time = time.strftime("%H:%M:%S")
st.session_state.time_data.append(current_time)
st.session_state.perf_data.append(perf)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=list(st.session_state.time_data),
    y=list(st.session_state.perf_data),
    mode='lines+markers',
    line=dict(width=4, color=ring_color),
    marker=dict(size=8, color=ring_color),
))

fig.update_layout(
    title="📈 Machine Performance Over Time",
    xaxis_title="Time",
    yaxis_title="Performance (%)",
    template="plotly_dark",
    height=400,
)

st.plotly_chart(fig, use_container_width=True)

# ------------------- AUTO REFRESH -------------------
time.sleep(2)
st.rerun()
