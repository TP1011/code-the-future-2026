'''
Acest fisier a fost preluat de la adresa https://github.com/ManuMerlo/AReS-Anesthesia-Response-Simulator/blob/main/python/notebooks/disturbance.ipynb

Acesta a fost ulterior modificat

Update: Acest fisier nu mai este utilizat in proiect (nu mai utilizam biblioteca AReS), dar reprezinta o referinta pentru proiectul nostru

'''

# External libraries import
import matplotlib.pyplot as plt

# Local libraries import
from AReS import Simulator, Model, Interaction, DoHMeasure, DisturbanceType, SimulatorMode, TciMode

stimuli = {
    1 * 60: (DisturbanceType.INTUBATION, 2 * 60, [1, 1, 1]), 
    5 * 60: (DisturbanceType.INCISION, 2 * 60, [10, 10, 20]),  
    10 * 60: (DisturbanceType.SKIN_MANIPULATION, 10 * 60, [5, 5,10]),
    21 * 60: (DisturbanceType.SUTURE, 5 * 60, [2, 2, 4]) 
}

interaction = Interaction.SURFACE
doh_measure = DoHMeasure.BOTH
t_sim = 30 * 60
t_s = 5
pk_models = {'prop': Model.ELEVELD, 'remi': Model.ELEVELD}
pd_models = {'prop': Model.PATIENT_SPECIFIC, 'remi': Model.ELEVELD}

simulator = Simulator.create(SimulatorMode.CONCENTRATION)
limits_TCI = {'cp_limit_prop': 10, 'cp_limit_remi': 10, 'infusion_limit_prop': 2,
              'infusion_limit_remi': 0.5}
modes_TCI = {'prop': TciMode.EFFECT_SITE, 'remi': TciMode.EFFECT_SITE}

t_prop = [2.0] * t_sim
t_remi = [3.6] * t_sim
t_nore = [0.5] * t_sim
t_rocu = [0.0] * t_sim

patient_id = 29
for idx, k in enumerate([patient_id, patient_id, patient_id,patient_id]):
    is_disturbed = (idx % 2 == 0)
    current_stimuli = stimuli if is_disturbed else None

    simulator.init_simulation_from_file(
        id_patient=k,
        t_sim=t_sim,
        t_s=t_s,
        pk_models=pk_models,
        pd_models=pd_models,
        pk_models_TCI=pk_models,
        pd_models_TCI=pd_models,
        modes_TCI= modes_TCI,
        interaction=interaction,
        doh_measure=doh_measure,
        seed_disturbance=30,
        stimuli=current_stimuli,
        limits_TCI=limits_TCI
    )

    simulator.run_complete_simulation(t_prop, t_remi, t_nore, t_rocu)
    simulator.save_simulation()

# Fetch all results after simulations
results = simulator.get_patient_results()

name = {'_CO_all': 'CO', '_WAV_all': 'WAV', '_MAP_all': 'MAP', '_HR_all': 'HR', '_cp_prop_all': 'cp_prop', '_cp_remi_all': 'cp_remi'}
units = {'_CO_all': '[L/min]', '_WAV_all': '', '_MAP_all': '[mmHg]', '_HR_all': '[bpm]', '_cp_prop_all': '[μg/mL]', '_cp_remi_all': '[ng/mL]'}
# Compare disturbed (i) vs undisturbed (i+1) for each pair
for i in range(0, 4, 2):
    print(f"\nPatient {patient_id}")
    for start, value in stimuli.items():
        disturbance_type, duration, params = value
        print(f" Disturbance: {disturbance_type.name}")
        for key in name:
            disturbed = results[key][i][start + duration]
            normal = results[key][i + 1][start + duration]
            diff = disturbed - normal
            print(f"    {name[key]}: {diff:.2f}")

