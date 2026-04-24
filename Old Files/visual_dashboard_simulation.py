import streamlit as st
import pandas as pd
import time
from gpiozero import DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory
import python_anesthesia_simulator as pas


st.set_page_config(page_title="Anesthesia", layout="wide")

@st.cache_resource
def init_sensor():
    factory = LGPIOFactory()
    return DistanceSensor(echo=24, trigger=23, max_distance=1.5, pin_factory=factory)

sensor = init_sensor()

INALTIME_TOTALA = 13.8
INALTIME_PAHAR = 8.0

def get_nivel_apa_real():
    try:
        distanta_citita = sensor.distance * 100
        nivel = INALTIME_TOTALA - distanta_citita
        return max(0, min(nivel, INALTIME_PAHAR))
    except Exception:
        return 0.0

st.sidebar.header("📋 Patient Configuration")
nume = st.sidebar.text_input("Patient Name", "John Doe")
varsta = st.sidebar.number_input("Age", 18, 100, 45)
inaltime = st.sidebar.number_input("Height (cm)", 100, 250, 175)
greutate = st.sidebar.number_input("Weight (kg)", 30, 200, 75)
sex_input = st.sidebar.selectbox("Sex", ["M", "F"])
sex = 1 if sex_input == "M" else 0

alegere = st.sidebar.radio("Primary Substance", ["Propofol", "Remifentanil"])
substanta_principala = "prop" if alegere == "Propofol" else "remi"

st.title(f"Digital Twin Monitoring: {nume}")

if 'pacient' not in st.session_state:
    ts = 5
    st.session_state.pacient = pas.Patient([varsta, inaltime, greutate, sex], ts=ts, co_update=False)
    st.session_state.pacient.initialized_at_maintenance(bis_target=98, tol_target=0.5, map_target=90)
    st.session_state.start_time = time.time()

pacient = st.session_state.pacient

col1, col2, col3 = st.columns(3)
m1 = col1.empty()
m2 = col2.empty()
m3 = col3.empty()
chart_placeholder = st.empty()

run_simulation = st.checkbox("Start Monitoring", value=True)

if run_simulation:
    while True:
        nivel_apa = get_nivel_apa_real()
        
        if substanta_principala == "prop":
            u_propo_val = nivel_apa 
            u_remi_val = u_propo_val * 0.02 + 0.01 
        else:
            u_remi_val = nivel_apa / 100.0
            u_propo_val = 20.0 

        pacient.one_step(u_propo=u_propo_val, u_remi=u_remi_val, u_nore=0.0, blood_rate=0.0, noise=True)
        
        vitals = pacient.dataframe.iloc[-1]
        bis_val = vitals.get('BIS', 100)

        if bis_val < 40: st_text, color = "VERY DEEP", "inverse"
        elif bis_val < 60: st_text, color = "OPTIMAL", "normal"
        elif bis_val < 85: st_text, color = "SEDATED", "normal"
        else: st_text, color = "AWAKE", "off"

        m1.metric("Water Level (cm)", f"{nivel_apa:.2f}")
        m2.metric("BIS Index", f"{bis_val:.1f}")
        m3.metric("Status", st_text)

        chart_placeholder.line_chart(pacient.dataframe[['BIS', 'MAP']].tail(50))

        time.sleep(1)