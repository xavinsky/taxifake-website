import streamlit as st
import requests
import pandas as pd
from datetime import date, time

'''
# TaxiFare Website 🚕
'''

st.markdown('''
Interface Streamlit qui appelle l'API de prediction de prix de course construite
dans le challenge precedent (`07-ML-Ops/04-Predict-in-production/data-fast-api`).
''')

'''
## Parametres de la course
'''

# Un seul champ pickup_datetime cote API (string "%Y-%m-%d %H:%M:%S") mais Streamlit
# separe naturellement date et heure en deux widgets, recombines plus bas
pickup_date = st.date_input('Date de la course', value=date(2014, 7, 6))
pickup_time = st.time_input('Heure de la course', value=time(19, 18))

# Valeurs par defaut = celles deja utilisees comme exemple par l'API (fast.py)
pickup_longitude = st.number_input('Longitude de prise en charge', value=-73.950655, format='%.6f')
pickup_latitude = st.number_input('Latitude de prise en charge', value=40.783282, format='%.6f')
dropoff_longitude = st.number_input('Longitude de depose', value=-73.984365, format='%.6f')
dropoff_latitude = st.number_input('Latitude de depose', value=40.769802, format='%.6f')

passenger_count = st.number_input('Nombre de passagers', min_value=1, max_value=8, value=2, step=1)

'''
## Appel a l'API pour recuperer une prediction
'''

# URL par defaut Le Wagon (dispo meme sans avoir deploye sa propre API)
url = 'https://taxifare-884258104866.europe-west1.run.app/predict'

if url == 'https://taxifare.lewagon.ai/predict':
    st.markdown('ℹ️ URL par defaut Le Wagon utilisee. Remplace `url` ci-dessus par `SERVICE_URL` '
                '(fichier `.env` de `07-ML-Ops/04-Predict-in-production/data-fast-api/`) pour appeler TON API.')

# Dictionnaire des parametres attendus par l'endpoint /predict (memes noms que taxifare/api/fast.py)
# pickup_date et pickup_time combines en un seul string "%Y-%m-%d %H:%M:%S"
params = dict(
    pickup_datetime=f'{pickup_date} {pickup_time}',
    pickup_longitude=pickup_longitude,
    pickup_latitude=pickup_latitude,
    dropoff_longitude=dropoff_longitude,
    dropoff_latitude=dropoff_latitude,
    passenger_count=int(passenger_count),
)

# Bouton plutot qu'un appel a chaque rerun de la page (Streamlit relance tout le
# script a chaque interaction) : evite de spammer l'API a chaque frappe clavier
if st.button('Estimer le prix de la course'):
    response = requests.get(url, params=params)
    prediction = response.json()
    fare = prediction['fare']
    st.markdown(f'## 💰 Prix estime : {fare:.2f} $')

'''
## Trajet sur la carte
'''

# st.map attend un DataFrame avec des colonnes lat/lon : ici les deux points
# (prise en charge et depose) pour visualiser le trajet
trip_df = pd.DataFrame({
    'lat': [pickup_latitude, dropoff_latitude],
    'lon': [pickup_longitude, dropoff_longitude],
})
st.map(trip_df)
