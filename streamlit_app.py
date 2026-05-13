import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime, timedelta

# Konfiguracja
st.set_page_config(page_title="BearAlert PRO", layout="wide", page_icon="🐻")
polski_czas = datetime.now() + timedelta(hours=2)

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# Geolokalizacja - zmiana User-Agent na unikalny losowy ciąg
geolocator = Nominatim(user_agent="bieszczady_bear_final_rescuetool_99")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

def pobierz_dane_bez_zawieszania():
    url = "https://esanok.pl/"
    # Zmieniony User-Agent na bardziej "ludzki"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    wyniki = []
    
    try:
        # Bardzo krótki timeout, żeby aplikacja "nie wisiała"
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code != 200:
            return pd.DataFrame()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # Skanujemy tylko główne nagłówki h2 i h3 (najszybsze)
        for tag in soup.find_all(['h2', 'h3']):
            tytul = tag.get_text().strip()
            if any(key in tytul.lower() for key in ["niedźwiedź", "niedźwiedzica", "niedźwiedzie"]):
                link_tag = tag.find('a')
                if not link_tag: continue
                link = link_tag['href']
                
                # Wykrywanie miejsca
                miejsca = ["Zahutyń", "Wołkowyja", "Tarnawa", "Sanok", "Lesko", "Zagórz", "Solina", "Huzele", "Płonna", "Myczków", "Brzozów", "Morochów"]
                wykryte = "Bieszczady"
                for m in miejsca:
                    if m.lower() in tytul.lower():
                        wykryte = m
                        break
                
                # Geokodowanie
                loc = geocode(f"{wykryte}, Podkarpackie, Polska")
                coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                
                wyniki.append({"Tytuł": tytul, "Miejsce": wykryte, "Link": link, "Coords": coords})
        
        return pd.DataFrame(wyniki).drop_duplicates(subset=['Link'])
    except:
        # W razie jakiegokolwiek błędu/blokady, zwróć pustą tabelę natychmiast
        return pd.DataFrame()

# Logika
if 'last_df' not in st.session_state:
    st.session_state.last_df = pd.DataFrame()

if st.sidebar.button("🔄 WYMUŚ SKANOWANIE"):
    st.session_state.last_df = pobierz_dane_bez_zawieszania()

# Automatyczne pobieranie przy starcie (tylko jeśli puste)
if st.session_state.last_df.empty:
    st.session_state.last_df = pobierz_dane_bez_zawieszania()

df = st.session_state.last_df

# Interfejs
st.title("🐻 BearAlert PRO: Monitoring Bieszczady")

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
                popup=f"<b>{row['Miejsce']}</b><br>{row['Tytuł']}<br><a href='{row['Link']}'>Link</a>",
                icon=folium.Icon(color='red', icon='warning', prefix='fa')
            ).add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_glowna")

with col_list:
    st.subheader("🚩 Ostatnie newsy")
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"📍 {row['Miejsce']}"):
                st.write(row['Tytuł'])
                st.link_button("Otwórz", row['Link'])
    else:
        st.info("Brak nowych danych (lub eSanok blokuje połączenie). Spróbuj kliknąć przycisk ODŚWIEŻ w pasku bocznym za chwilę.")
