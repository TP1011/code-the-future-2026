
'''
    Acest fisier reprezinta programul principal de simulare

    A fost utilizata biblioteca Python Anesthesia Simulator

    Link: https://github.com/BobAubouin/Python_Anesthesia_Simulator/tree/main

'''

import streamlit as st
import pandas as pd
import time
import numpy as np
from gpiozero import DistanceSensor, Servo
from gpiozero.pins.lgpio import LGPIOFactory
import python_anesthesia_simulator as pas

st.set_page_config(page_title="Anesthesia Digital Twin", layout="wide")

@st.cache_resource
def init_hardware():
    try:
        factory = LGPIOFactory()
        s_dist = DistanceSensor(echo=24, trigger=23, max_distance=1.5, pin_factory=factory)
        s_servo = Servo(12, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)
        s_servo.detach()
        return s_dist, s_servo
    except Exception as e:
        st.error(f"Eroare Hardware: {e}")
        return None, None

sensor, servo = init_hardware()

if 'ekg_buffer' not in st.session_state:
    st.session_state.ekg_buffer = [0.0] * 100
if 'ekg_counter' not in st.session_state:
    st.session_state.ekg_counter = 0
if 'last_servo_state' not in st.session_state:
    st.session_state.last_servo_state = None

INALTIME_TOTALA = 14.25 
INALTIME_PAHAR = 8.0
PRAG_SERINGA = 0.1 

def get_nivel_apa_real():
    if sensor is None: return 0.0
    try:
        distanta_citita = sensor.distance * 100
        nivel = INALTIME_TOTALA - distanta_citita
        return max(0, min(nivel, INALTIME_PAHAR))
    except Exception:
        return 0.0

st.sidebar.header("📋 Patient Configuration")
nume = st.sidebar.text_input("Patient Name", "Marin Popescu")
varsta = st.sidebar.number_input("Age", 18, 100, 45)
inaltime = st.sidebar.number_input("Height (cm)", 100, 250, 175)
greutate = st.sidebar.number_input("Weight (kg)", 30, 200, 75)
sex_input = st.sidebar.selectbox("Sex", ["M", "F"])
sex = 1 if sex_input == "M" else 0

alegere = st.sidebar.radio("Primary Substance", ["Propofol"])
substanta_principala = "prop" if alegere == "Propofol" else "remi"

st.title(f"Hospital Monitor : {nume}")

if 'pacient' not in st.session_state:
    ts = 5
    st.session_state.pacient = pas.Patient([varsta, inaltime, greutate, sex], ts=ts, co_update=False)
    st.session_state.pacient.initialized_at_maintenance(bis_target=98, tol_target=0.5, map_target=90)

pacient = st.session_state.pacient

col1, col2, col3, col4 = st.columns(4)
m1 = col1.empty()
m2 = col2.empty()
m3 = col3.empty()
m4 = col4.empty()

st.markdown("---")
g_col1, g_col2 = st.columns([2, 1])
chart_placeholder = g_col1.empty()
ekg_placeholder = g_col2.empty()

st.sidebar.markdown("---")
st.sidebar.subheader("💉 Syringe Pump Status")
syringe_status = st.sidebar.empty()

run_simulation = st.checkbox("Start Monitoring & Pump Control", value=True)

if run_simulation:
    while True:
        nivel_apa = get_nivel_apa_real()
        
        if servo:
            current_state = "max" if nivel_apa > PRAG_SERINGA else "min"
            
            if current_state != st.session_state.last_servo_state:
                if current_state == "max":
                    servo.max()
                    syringe_status.success("ACTIVE (Injecting)")
                else:
                    servo.min()
                    syringe_status.warning("IDLE (Released)")
             
                st.session_state.last_servo_state = current_state
                
                time.sleep(0.4) 
                servo.detach() 
            else:
                if current_state == "max":
                    syringe_status.success("ACTIVE (Holding Position)")
                else:
                    syringe_status.warning("IDLE (Sleeping)")

        if substanta_principala == "prop":
            u_propo_val = nivel_apa 
            u_remi_val = u_propo_val * 0.02 + 0.01 
        else:
            u_remi_val = nivel_apa / 100.0
            u_propo_val = 20.0 

        pacient.one_step(u_propo=u_propo_val, u_remi=u_remi_val, u_nore=0.0, blood_rate=0.0, noise=True)
        vitals = pacient.dataframe.iloc[-1]
        bis_val = vitals.get('BIS', 100)
     
        bpm = 50 + (bis_val / 100) * 40
        for _ in range(10):
            st.session_state.ekg_counter += 1
            frecventa_bataie = (60 / bpm) * 10
            pozitie_in_ciclu = st.session_state.ekg_counter % frecventa_bataie
            if 0 < pozitie_in_ciclu < 1: point = 1.5
            elif 1 <= pozitie_in_ciclu < 2: point = -0.3
            else: point = 0.0
            point += np.random.normal(0, 0.03)
            st.session_state.ekg_buffer.append(point)
            st.session_state.ekg_buffer = st.session_state.ekg_buffer[-100:]

     
        if bis_val < 40: st_text = "VERY DEEP"
        elif bis_val < 60: st_text = "OPTIMAL"
        elif bis_val < 85: st_text = "SEDATED"
        else: st_text = "AWAKE"

        m1.metric("Anesthesia Level", f"{nivel_apa:.1f} cm")
        m2.metric("BIS Index", f"{bis_val:.1f}")
        m3.metric("Status", st_text)
        m4.metric("Heart Rate", f"{int(bpm)} BPM")

        chart_placeholder.line_chart(pacient.dataframe[['BIS', 'MAP']].tail(50))
        ekg_df = pd.DataFrame(st.session_state.ekg_buffer, columns=["EKG"])
        ekg_placeholder.line_chart(ekg_df, height=250, use_container_width=True)

        time.sleep(0.2)