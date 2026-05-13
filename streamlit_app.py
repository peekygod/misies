import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime

# 1. KONFIGURACJA STRONY
st.set_page_config(page_title="BearAlert: Twoja Mapa", layout="wide", page_icon="🐻")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# 2. TWOJA LISTA INCYDENTÓW (TUTAJ DOPISUJESZ NOWE)
# Możesz edytować poniższą listę. Pamiętaj o przecinkach i cudzysłowach!
dane_od_uzytkownika = [
    {
        "data": "12.05.2026 08:30",
        "miejsce": "Zahutyń",
        "opis": "Niedźwiedź widziany przy drodze krajowej, ruszył w stronę posesji.",
        "link": "https://esanok.pl"
    },
    {
        "data": "11.05.2026 19:15",
        "miejsce": "Wołkowyja",
        "opis": "Atak na pasiekę obok domów mieszkalnych.",
        "link": "https://esanok.pl"
    },
    {
        "data": "10.05.2026 22:00",
        "miejsce": "Tarnawa",
        "opis": "Niedźwiedzica z młodymi spacerowała pod oknami mieszkańców.",
        "link": "https://esanok.pl"
    },
    # Aby dodać nowy, skopiuj poniższe i wklej powyżej tego nawiasu:
    # {"data": "DATA", "miejsce": "MIEJSCOWOŚĆ", "opis": "OPIS", "link": "LINK"},
]

# 3. LOGIKA MAPY
geolocator = Nominatim(user_agent="bear_manual_map_v1")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.5)

@st.cache_data
def przygotuj_punkty(lista):
    punkty = []
    for item in lista:
        loc = geolocator.geocode(f"{item['miejsce']}, Podkarpackie, Polska")
        if loc:
            item['coords'] = [loc.latitude, loc.longitude]
            punkty.append(item)
    return punkty

punkty_na_mapie = przygotuj_punkty(dane_od_uzytkownika)

# 4. INTERFEJS UŻYTKOWNIKA
st.title("🐻 BearAlert: Panel Monitorowania")
st.subheader("Ręczne nanoszenie zagrożeń na mapę")

col_map, col_list = st.columns([2, 1])

with col_map:
    # Interaktywna ciemna mapa
    m = folium.Map(location=[49.46, 22.35], zoom_start=11, tiles='CartoDB dark_matter')
    
    for p in punkty_na_mapie:
        html = f"""
        <div style="font-family: Arial; color: black; min-width: 150px;">
            <h4 style="margin:0; color:red;">{p['miejsce']}</h4>
            <p style="font-size:12px; margin:5px 0;"><b>{p['data']}</b></p>
            <p style="font-size:11px;">{p['opis']}</p>
            <a href="{p['link']}" target="_blank">Otwórz artykuł</a>
        </div>
        """
        folium.Marker(
            location=p['coords'],
            popup=folium.Popup(html, max_width=250),
            tooltip=f"{p['miejsce']} - {p['data']}",
            icon=folium.Icon(color='red', icon='warning', prefix='fa')
        ).add_to(m)
    
    st_folium(m, width="100%", height=550)

with col_list:
    st.metric("Zarejestrowane punkty", len(punkty_na_mapie))
    st.divider()
    st.subheader("📜 Lista zdarzeń")
    for p in punkty_na_mapie:
        with st.expander(f"🔴 {p['data']} - {p['miejsce']}"):
            st.write(p['opis'])
            st.link_button("Zobacz źródło", p['link'])

st.info("💡 Aby dodać nowy punkt, edytuj plik streamlit_app.py na GitHubie w sekcji 'dane_od_uzytkownika'.")
