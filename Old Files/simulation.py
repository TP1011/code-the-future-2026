from gpiozero import DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory
import python_anesthesia_simulator as pas
import time

factory = LGPIOFactory()

sensor = DistanceSensor(echo=24, trigger=23, max_distance=1.5, pin_factory=factory)

INALTIME_TOTALA = 13.8  
INALTIME_PAHAR = 8.0    

def get_nivel_apa_real():
    try:
        distanta_citita = sensor.distance * 100
        nivel = INALTIME_TOTALA - distanta_citita
        if nivel < 0: nivel = 0
        if nivel > INALTIME_PAHAR: nivel = INALTIME_PAHAR
        return nivel
    except Exception:
        return 0.0

print("=== CONFIGURARE PACIENT DIGITAL TWIN ===")
nume = input("Nume Pacient: ")
varsta = float(input("Vârstă (ani): "))
inaltime = float(input("Înălțime (cm): "))
greutate = float(input("Greutate (kg): "))
sex = 1 if input("Sex (M/F): ").upper() == 'M' else 0

print("\n=== CONFIGURARE TERAPIE ===")
print("1. PROPOFOL (Control prin nivel apă)")
print("2. REMIFENTANIL (Control prin nivel apă)")
alegere = input("Alegere (1/2): ")
substanta_principala = "prop" if alegere == "1" else "remi"

ts = 5 
pacient = pas.Patient([varsta, inaltime, greutate, sex], ts=ts, co_update=False)

print(f"\nStabilizare {nume} (Digital Twin)...")

pacient.initialized_at_maintenance(bis_target=98, tol_target=0.5, map_target=90)

print("\n" + "="*115)
print(f"{'TIMP':<7} | {'APA (cm)':<10} | {'PROP (ug/kg/min)':<18} | {'REMI (ug/kg/min)':<18} | {'BIS':<6} | {'STATUS'}")
print("="*115)

current_step = 0

try:
    while True:
        loop_start = time.time()
        
        nivel_apa = get_nivel_apa_real()

        if substanta_principala == "prop":
            u_propo_val = nivel_apa 
            u_remi_val = u_propo_val * 0.02 + 0.01 
        else:
            u_remi_val = nivel_apa / 100.0
            u_propo_val = 20.0 

        pacient.one_step(
            u_propo=u_propo_val,
            u_remi=u_remi_val,
            u_nore=0.0,
            blood_rate=0.0,
            noise=True
        )

        vitals = pacient.dataframe.iloc[-1]
        bis_val = vitals.get('BIS', 100)

        if bis_val < 40: st = "ANESTEZIE FOARTE PROFUNDĂ"
        elif bis_val < 60: st = "ANESTEZIE OPTIMĂ"
        elif bis_val < 85: st = "SEDAT"
        else: st = "TREAZ"

        print(f"{current_step*ts:>5.1f}s | "
              f"{nivel_apa:>10.1f} | "
              f"{u_propo_val:>17.2f} | "
              f"{u_remi_val:>17.3f} | "
              f"{bis_val:>6.1f} | "
              f"{st}")

        current_step += 1
        wait = max(0, ts - (time.time() - loop_start))
        time.sleep(wait)

except KeyboardInterrupt:
    print(f"\nSalvare date pentru {nume}...")
    pacient.dataframe.to_csv(f"twin_{nume}.csv")