import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime, timedelta

# 1. Konfiguracja strefy czasowej i wyglądu
st.set_page_config(page_title="BearAlert Bieszczady", layout="wide", page_icon="🐻")
# Poprawka czasu dla Polski
polski_czas = datetime.now() + timedelta(hours=2)

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# 2. Narzędzia lokalizacji (z unikalnym agentem, by uniknąć blokad)
geolocator = Nominatim(user_agent="bieszczady_bear_monitor_final_v8")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

def pobierz_dane_bezpieczne():
    # Używamy strony głównej - najmniejsza szansa na blokadę
    url = "https://esanok.pl/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'}
    wyniki = []
    
    try:
        # Krótki timeout (5 sekund), żeby aplikacja nie kręciła się w nieskończoność
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukamy nagłówków z ostatnich newsów
        artykuły = soup.find_all(['h1', 'h2', 'h3'])
        
        for art in artykuły:
            tytul = art.text.strip()
            # Szukamy słów kluczowych
            if any(word in tytul.lower() for word in ["niedźwiedź", "niedźwiedzica", "ataku", "grasuje"]):
                link_tag = art.find('a')
                if not link_tag: continue
                link = link_tag['href']
                
                # Prosta logika wyciągania miejscowości
                miejsca = ["Zahutyń", "Wołkowyja", "Tarnawa", "Sanok", "Lesko", "Zagórz", "Solina", "Ustrzyki", "Huzele", "Płonna", "Myczków", "Olchowce", "Brzozów", "Morochów"]
                wykryte_miejsce = "Bieszczady"
                for m in miejsca:
                    if m.lower() in tytul.lower():
                        wykryte_miejsce = m
                        break
                
                # Szybkie geokodowanie
                loc = geocode(f"{wykryte_miejsce}, Podkarpackie, Polska")
                coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                
                wyniki.append({
                    "Tytuł": tytul,
                    "Miejsce": wykryte_miejsce,
                    "Link": link,
                    "Coords": coords
                })
        
        return pd.DataFrame(wyniki).drop_duplicates(subset=['Link'])
    except Exception as e:
        st.error(f"Nie udało się połączyć z eSanok (Timeout). Spróbuj odświeżyć stronę za chwilę.")
        return pd.DataFrame()

# 3. Logika Dashboardu
if 'data_bear' not in st.session_state or st.sidebar.button("🔄 ODŚWIEŻ MAPĘ"):
    with st.spinner('Łączenie z serwerem eSanok...'):
        st.session_state.data_bear = pobierz_dane_bezpieczne()

df = st.session_state.data_bear

# --- WYŚWIETLANIE ---
st.title("🐻 BearAlert PRO: Monitoring eSanok")

c1, c2, c3 = st.columns(3)
with c1: st.metric("System", "Online 🟢")
with c2: st.metric("Znalezione alerty", len(df))
with c3: st.metric("Czas (PL)", polski_czas.strftime("%H:%M"))

col_map, col_list = st.columns([2, 1])

with col_map:
    m = folium.Map(location=[49.46, 22.35], zoom_start=11, tiles='CartoDB dark_matter')
    if not df.empty:
        for _, row in df.iterrows():
            folium.Marker(
                location=row['Coords'],
                popup=f"<b>{row['Miejsce']}</b><br>{row['Tytuł']}<br><a href='{row['Link']}' target='_blank'>Czytaj więcej</a>",
                icon=folium.Icon(color='red', icon='warning', prefix='fa')
            ).add_to(m)
    st_folium(m, width="100%", height=500)

with col_list:
    st.subheader("🚩 Najnowsze newsy")
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"📍 {row['Miejsce']}"):
                st.write(row['Tytuł'])
                st.link_button("Otwórz artykuł", row['Link'])
    else:
        st.info("Brak nowych artykułów o niedźwiedziach na stronie głównej eSanok.")
