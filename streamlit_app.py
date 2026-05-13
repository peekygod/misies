import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime, timedelta

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
geolocator = Nominatim(user_agent="bear_alert_bieszczady_v6")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

def wyciagnij_miejsce(tekst):
    """Szybkie wyciąganie miejscowości z tytułu na podstawie słownika"""
    miejscowosci = ["Zahutyń", "Wołkowyja", "Tarnawa", "Sanok", "Lesko", "Zagórz", "Solina", "Ustrzyki", "Bereźnica", "Huzele", "Płonna", "Bukowsko", "Domaradz", "Myczków", "Olchowce"]
    # Naprawa najczęstszych odmian z eSanok
    tekst_poprawiony = tekst.replace("Zahutyniu", "Zahutyń").replace("Wołkowyi", "Wołkowyja").replace("Tarnawie", "Tarnawa").replace("Bereźnicy", "Bereźnica").replace("Myczkowie", "Myczków").replace("Domaradzu", "Domaradz")
    
    for m in miejscowosci:
        if m.lower() in tekst_poprawiony.lower():
            return m
    return "Bieszczady"

def pobierz_dane_stabilne():
    # Szukamy bezpośrednio po frazie niedźwiedź
    url = "https://esanok.pl/?s=niedźwiedź"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    wyniki = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pobieramy nagłówki h2 (tytuły artykułów)
        artykuly = soup.find_all('h2', class_='entry-title')
        
        for art in artykuly:
            tytul = art.text.strip()
            link_tag = art.find('a')
            if not link_tag: continue
            link = link_tag['href']
            
            # Filtracja - tylko realne newsy o niedźwiedziach
            if any(slowo in tytul.lower() for slowo in ["niedźwiedź", "niedźwiedzica", "drapieżnik"]):
                miejsce = wyciagnij_miejsce(tytul)
                
                # Geokodowanie
                loc = geocode(f"{miejsce}, Podkarpackie, Polska")
                coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                
                wyniki.append({
                    "Tytuł": tytul,
                    "Miejsce": miejsce,
                    "Link": link,
                    "Coords": coords
                })
        return pd.DataFrame(wyniki)
    except Exception as e:
        st.sidebar.error(f"Błąd połączenia: {e}")
        return pd.DataFrame()

# Logika pobierania
if 'df_v6' not in st.session_state or st.sidebar.button("🔄 ODŚWIEŻ RAPORTY"):
    with st.spinner('Pobieram najnowsze dane z eSanok...'):
        st.session_state.df_v6 = pobierz_dane_stabilne()

df = st.session_state.df_v6

# --- DASHBOARD ---
st.title("🐻 BearAlert PRO: Monitoring Zagrożeń")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Status Systemu", "Aktywny 🟢")
with c2:
    st.metric("Liczba alertów", len(df))
with c3:
    st.metric("Czas skanowania (PL)", polski_czas.strftime("%H:%M"))

col_map, col_info = st.columns([2, 1])

with col_map:
    # Ciemna mapa
    m = folium.Map(location=[49.46, 22.35], zoom_start=11, tiles='CartoDB dark_matter')
    
    if not df.empty:
        for _, row in df.iterrows():
            popup_html = f"<div style='color:black;'><b>{row['Miejsce']}</b><br>{row['Tytuł']}<br><a href='{row['Link']}' target='_blank'>Otwórz artykuł</a></div>"
            folium.Marker(
                location=row['Coords'],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
            ).add_to(m)
    st_folium(m, width="100%", height=500)

with col_info:
    st.subheader("🚩 Najnowsze komunikaty")
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"📍 {row['Miejsce']}"):
                st.write(row['Tytuł'])
                st.link_button("Czytaj na eSanok", row['Link'])
    else:
        st.warning("Nie znaleziono nowych artykułów. Spróbuj odświeżyć za chwilę.")
