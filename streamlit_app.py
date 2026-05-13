import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime, timedelta
import time

# Konfiguracja strefy czasowej i strony
st.set_page_config(page_title="BearAlert PRO", layout="wide", page_icon="🐻")
polski_czas = datetime.now() + timedelta(hours=2)

# Stylizacja
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# Geolokalizacja
geolocator = Nominatim(user_agent="bieszczady_bear_final_fix")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.2)

def wyciagnij_miejsce(tekst):
    regiony = ["Zahutyń", "Wołkowyja", "Tarnawa", "Sanok", "Lesko", "Zagórz", "Solina", "Ustrzyki", "Bereźnica", "Huzele", "Płonna", "Bukowsko", "Morochów", "Myczków", "Brzozów"]
    tekst_popr = tekst.replace("Zahutyniu", "Zahutyń").replace("Wołkowyi", "Wołkowyja").replace("Morochowie", "Morochów").replace("Płonnej", "Płonna")
    for r in regiony:
        if r.lower() in tekst_popr.lower():
            return r
    return "Bieszczady"

def pobierz_dane_bezposrednie():
    # Skanujemy stronę główną i działy zamiast wyszukiwarki (to omija blokady)
    urls = ["https://esanok.pl/", "https://esanok.pl/category/wiadomosci"]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    znaleziska = []
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Szukamy linków w nagłówkach h1, h2, h3
            for tag in soup.find_all(['h1', 'h2', 'h3']):
                tytul = tag.text.strip()
                link_tag = tag.find('a')
                if link_tag and any(slowo in tytul.lower() for slowo in ["niedźwiedź", "niedźwiedzica", "drapieżnik"]):
                    link = link_tag['href']
                    if not link.startswith('http'): link = "https://esanok.pl" + link
                    
                    miejsce = wyciagnij_miejsce(tytul)
                    loc = geocode(f"{miejsce}, Podkarpackie, Polska")
                    coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                    
                    znaleziska.append({
                        "Tytuł": tytul,
                        "Miejsce": miejsce,
                        "Link": link,
                        "Coords": coords,
                        "Data": polski_czas.strftime("%H:%M")
                    })
            time.sleep(1) # Delikatna przerwa
        except:
            continue
            
    df = pd.DataFrame(znaleziska).drop_duplicates(subset=['Link']) if znaleziska else pd.DataFrame()
    return df

# Logika Streamlit
if 'df_final' not in st.session_state or st.sidebar.button("🔄 WYMUŚ ODŚWIEŻANIE"):
    with st.spinner('Skanuję portal eSanok...'):
        st.session_state.df_final = pobierz_dane_bezposrednie()

df = st.session_state.df_final

# --- DASHBOARD ---
st.title("🐻 BearAlert PRO: Monitoring Zagrożeń")

c1, c2, c3 = st.columns(3)
with c1: st.metric("System", "Online 🟢")
with c2: st.metric("Alerty", len(df))
with c3: st.metric("Aktualizacja", polski_czas.strftime("%H:%M"))

col_map, col_info = st.columns([2, 1])

with col_map:
    m = folium.Map(location=[49.46, 22.35], zoom_start=11, tiles='CartoDB dark_matter')
    if not df.empty:
        for _, row in df.iterrows():
            folium.Marker(
                location=row['Coords'],
                popup=f"<b>{row['Miejsce']}</b><br>{row['Tytuł']}<br><a href='{row['Link']}'>Link</a>",
                icon=folium.Icon(color='red', icon='warning', prefix='fa')
            ).add_to(m)
    st_folium(m, width="100%", height=500)

with col_info:
    st.subheader("🚩 Ostatnie newsy")
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"📍 {row['Miejsce']}"):
                st.write(row['Tytuł'])
                st.link_button("Czytaj artykuł", row['Link'])
    else:
        st.warning("Portal eSanok nie udostępnił nowych danych w tej chwili. Spróbuj za 5 minut.")
