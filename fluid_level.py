from gpiozero import DistanceSensor
from time import sleep

# Configurăm pinii (Trig=23, Echo=24)
sensor = DistanceSensor(echo=24, trigger=23, max_distance=1.0)

# DATELE TALE
INALTIME_TOTALA = 14.8  # Distanța senzor -> fundul paharului
INALTIME_PAHAR = 8    # Înălțimea efectivă a paharului

print("--- Monitorizare Nivel Pahar (8cm) ---")

try:
    while True:
        distanta_citita = sensor.distance * 100
        
        # Calculăm câți cm de apă sunt în pahar
        nivel_apa = INALTIME_TOTALA - distanta_citita
        
        # Limităm nivelul între 0 și înălțimea maximă a paharului
        if nivel_apa < 0: nivel_apa = 0
        if nivel_apa > INALTIME_PAHAR: nivel_apa = INALTIME_PAHAR
        
        # Calculăm procentul raportat DOAR la înălțimea paharului
        procent = (nivel_apa / INALTIME_PAHAR) * 100
        
        print(f"Senzorul vede suprafața la: {distanta_citita:.1f} cm")
        print(f"Nivel apă în pahar: {nivel_apa:.1f} cm / {INALTIME_PAHAR} cm")
        print(f"Procent: {procent:.1f}%")
        print("-" * 30)
        
        sleep(0.5)

except KeyboardInterrupt:
    print("\nProgram oprit.")