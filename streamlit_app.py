import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime, timedelta
import re

# Konfiguracja strony
st.set_page_config(page_title="BearAlert PRO", layout="wide", page_icon="🐻")

# Naprawa czasu dla Polski (UTC + 2h)
polski_czas = datetime.now() + timedelta(hours=2)

# Stylizacja Dashboardu
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# Narzędzia lokalizacji
geolocator = Nominatim(user_agent="bear_alert_bieszczady_v5")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

def wyciagnij_miejsce(tekst):
    """Szybkie wyciąganie miejscowości z tytułu"""
    miejscowosci = ["Zahutyń", "Wołkowyja", "Tarnawa", "Sanok", "Lesko", "Zagórz", "Solina", "Ustrzyki", "Bereźnica", "Huzele", "Płonna", "Bukowsko"]
    # Naprawa odmian
    tekst = tekst.replace("Zahutyniu", "Zahutyń").replace("Wołkowyi", "Wołkowyja").replace("Tarnawie", "Tarnawa").replace("Bereźnicy", "Bereźnica")
    for m in miejscowosci:
        if m.lower() in tekst.lower():
            return m
    return "Bieszczady"

def pobierz_dane_stabilne():
    url = "https://esanok.pl/?s=niedźwiedź"
    headers = {'User-Agent': 'Mozilla/5.0'}
    wyniki = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Szukamy nagłówków artykułów
        artykuly = soup.find_all('h2', class_='entry-title')
        
        for art in artykuly:
            tytul = art.text.strip()
            link = art.find('a')['href']
            
            # Tylko jeśli artykuł faktycznie jest o niedźwiedziu
            if "niedźwiedź" in tytul.lower() or "niedźwiedzica" in tytul.lower():
                miejsce = wyciagnij_miejsce(tytul)
                
                # Geokodowanie
                loc = geocode(f"{miejsce}, Podkarpackie, Polska")
                coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                
                wyniki.append({
                    "Tytuł": tytul,
                    "Miejsce": miejsce,
                    "Link": link,
                    "Coords": coords,
                    "Czas": polski_czas.strftime("%H:%M") # Czas pobrania informacji
                })
        return pd.DataFrame(wyniki)
    except:
        return pd.DataFrame()

# Pobieranie danych
if 'df_v5' not in st.session_state or st.sidebar.button("🔄 ODŚWIEŻ DANE"):
    with st.spinner('Synchronizacja z eSanok...'):
        st.session_state.df_v5 = pobierz_dane_stabilne()

df = st.session_state.df_v5

# --- LAYOUT ---
st.title("🐻 BearAlert: Monitorowanie Zagrożeń")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Status Systemu", "Aktywny 🟢")
with c2:
    st.metric("Wykryte Incydenty", len(df))
with c3:
    st.metric("Ostatni skan (Czas PL)", polski_czas.strftime("%H:%M"))

col_map, col_info = st.columns([2, 1])

with col_map:
    # Ciemna, interaktywna mapa
    m = folium.Map(location=[49.46, 22.35], zoom_start=11, tiles='CartoDB dark_matter')
    
    if not df.empty:
        for _, row in df.iterrows():
            popup_html = f"""
            <div style='color:black; min-width:150px;'>
                <b>{row['Miejsce']}</b><br>
                {row['Tytuł']}<br>
                <a href='{row['Link']}' target='_blank'>Zobacz artykuł</a>
            </div>
            """
            folium.Marker(
                location=row['Coords'],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
            ).add_to(m)
    st_folium(m, width="100%", height=500)

with col_info:
    st.subheader("🚩 Ostatnie doniesienia")
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"📍 {row['Miejsce']}"):
                st.write(row['Tytuł'])
                st.link_button("Otwórz eSanok", row['Link'])
    else:
        st.error("Brak danych. Sprawdź połączenie z esanok.pl")

st.caption("Aplikacja analizuje nagłówki serwisu eSanok.pl w czasie rzeczywistym.")
