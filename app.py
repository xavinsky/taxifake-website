import streamlit as st
import requests
import pandas as pd
from datetime import date, time
import folium
from streamlit_folium import st_folium

# layout='wide' pour avoir la place de mettre la carte a cote du formulaire
st.set_page_config(page_title='Taxifare - xavinsky', page_icon='🚕', layout='wide')

# Banderole image en tete de page, remplace le bandeau CSS texte precedent
st.image('assets/taxifare_banner.png', use_container_width=True)

# CSS custom : juste la carte resultat coloree desormais (le bandeau est l'image ci-dessus)
st.markdown('''
<style>
.result-card {
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin: 1.5rem 0;
}
.result-card .fare {
    font-size: 2.6rem;
    font-weight: 700;
    margin: 0;
    color: #1A1A1A;
}
.result-card .comment {
    font-size: 1rem;
    margin: 0.3rem 0 0 0;
    color: #1A1A1A;
}
</style>
''', unsafe_allow_html=True)

# Coordonnees par defaut = celles deja utilisees comme exemple par l'API (fast.py)
# Stockees dans st.session_state (pas en simples variables) pour pouvoir etre
# mises a jour aussi bien par un clic sur la carte que par saisie manuelle
for key, default in [
    ('pickup_longitude', -73.950655),
    ('pickup_latitude', 40.783282),
    ('dropoff_longitude', -73.984365),
    ('dropoff_latitude', 40.769802),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Carte a cote du formulaire (pas en dessous) : deux colonnes de meme largeur
col_form, col_map = st.columns(2)

with col_map:
    # Choix du point que le PROCHAIN clic sur la carte va deplacer : icones
    # colorees (vert/rouge) reprenant directement les couleurs des marqueurs
    # de la carte, plutot qu'un libelle texte
    click_target = st.radio(
        'Point à définir', ['🟢', '🔴'],
        horizontal=True, label_visibility='collapsed',
    )

    # Carte centree sur New York, avec les deux points actuels
    # (vert = prise en charge, rouge = depose), reconstruite a chaque rerun
    # avec les coordonnees courantes de st.session_state
    m = folium.Map(location=[40.75, -73.97], zoom_start=12)
    folium.Marker(
        [st.session_state.pickup_latitude, st.session_state.pickup_longitude],
        tooltip='Prise en charge', icon=folium.Icon(color='green'),
    ).add_to(m)
    folium.Marker(
        [st.session_state.dropoff_latitude, st.session_state.dropoff_longitude],
        tooltip='Dépose', icon=folium.Icon(color='red'),
    ).add_to(m)

    map_data = st_folium(m, height=420, width=560)

    # st_folium renvoie le dernier clic a CHAQUE rerun : on ne traite que s'il
    # est different du dernier clic deja applique, pour eviter une boucle infinie
    clicked = map_data.get('last_clicked')
    if clicked and clicked != st.session_state.get('last_clicked_processed'):
        st.session_state.last_clicked_processed = clicked
        if click_target == '🟢':
            st.session_state.pickup_latitude = clicked['lat']
            st.session_state.pickup_longitude = clicked['lng']
        else:
            st.session_state.dropoff_latitude = clicked['lat']
            st.session_state.dropoff_longitude = clicked['lng']
        # Rerun immediat pour que la carte et les champs numeriques ci-contre
        # affichent tout de suite le nouveau point (sinon visible seulement
        # au prochain rerun naturel)
        st.rerun()

with col_form:
    st.markdown('**Quand**')
    # Date, heure et passagers sur une seule ligne (3 sous-colonnes) plutot
    # qu'empiles verticalement
    col_date, col_time, col_pax = st.columns(3)
    with col_date:
        pickup_date = st.date_input('Date', value=date(2014, 7, 6))
    with col_time:
        pickup_time = st.time_input('Heure', value=time(19, 18))
    with col_pax:
        passenger_count = st.number_input('Passagers', min_value=1, max_value=8, value=2, step=1)

    # URL par defaut Le Wagon (dispo meme sans avoir deploye sa propre API)
    # Remplacer par ta propre SERVICE_URL (07-ML-Ops/04-Predict-in-production/data-fast-api/.env) pour utiliser TON API
    url = 'https://taxifare.lewagon.ai/predict'

    # Dictionnaire des parametres attendus par l'endpoint /predict (memes noms que taxifare/api/fast.py)
    # pickup_date et pickup_time combines en un seul string "%Y-%m-%d %H:%M:%S"
    params = dict(
        pickup_datetime=f'{pickup_date} {pickup_time}',
        pickup_longitude=st.session_state.pickup_longitude,
        pickup_latitude=st.session_state.pickup_latitude,
        dropoff_longitude=st.session_state.dropoff_longitude,
        dropoff_latitude=st.session_state.dropoff_latitude,
        passenger_count=int(passenger_count),
    )

    # Historique des estimations de la session, initialise une seule fois
    # (survit aux reruns Streamlit tant que l'onglet reste ouvert)
    if 'history' not in st.session_state:
        st.session_state.history = []

    # Bouton + resultat sous les parametres, dans la meme colonne que le
    # formulaire (a cote de la carte) plutot que sur toute la largeur en dessous
    # Bouton plutot qu'un appel a chaque rerun de la page (Streamlit relance tout le
    # script a chaque interaction) : evite de spammer l'API a chaque frappe clavier
    if st.button('Estimer le prix de la course', use_container_width=True):
        response = requests.get(url, params=params)
        prediction = response.json()
        fare = prediction['fare']

        # Couleur de la carte resultat + commentaire selon le prix, pour rendre
        # le resultat plus parlant qu'un simple chiffre
        if fare < 10:
            card_color, comment = '#E8F8E8', '🥳 Bon plan, cette course ne coute pas cher !'
        elif fare < 25:
            card_color, comment = '#FFF6DC', '🚕 Prix dans la moyenne pour un trajet a New York.'
        else:
            card_color, comment = '#FBE3E3', '💸 Aie, ca pique un peu pour cette course.'

        st.markdown(f'''
        <div class="result-card" style="background-color: {card_color};">
            <p class="fare">{fare:.2f} $</p>
            <p class="comment">{comment}</p>
        </div>
        ''', unsafe_allow_html=True)

        # Ajout de cette estimation a l'historique de la session
        st.session_state.history.append({
            'heure': pickup_time.strftime('%H:%M'),
            'passagers': int(passenger_count),
            'prix': round(fare, 2),
        })

# Historique range dans un expander (replie par defaut) pour ne pas surcharger la page
if st.session_state.history:
    with st.expander(f'🕓 Historique de la session ({len(st.session_state.history)})'):
        st.dataframe(pd.DataFrame(st.session_state.history), hide_index=True)
