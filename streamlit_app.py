import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="BearAlert: Bieszczady", layout="wide", page_icon="🐻")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# 2. TWOJA BAZA DANYCH (Ręczne wpisywanie - brak ryzyka błędu)
# Koordynaty znajdziesz w Google Maps klikając prawym przyciskiem na mapę
incydenty = [
    {
        "data": "12.05.2026",
        "miejsce": "Wołkowyja",
        "coords": [49.3333, 22.4333],
        "opis": "Wizyta niedźwiedzicy na posesji tuż obok maszyn rolniczych i domu.",
        "link": "https://esanok.pl/2026/wizyta-na-posesji-w-wolkowyi-video.html"
    },
    {
        "data": "12.05.2026",
        "miejsce": "Zahutyń",
        "coords": [49.5415, 22.2536],
        "opis": "Niedźwiedź widziany w okolicy 'dołu wioski', blisko sklepu i wjazdu w boczną ulicę.",
        "link": "https://esanok.pl"
    },
    {
        "data": "12.05.2026",
        "miejsce": "Bereźnica Wyżna",
        "coords": [49.3833, 22.3333],
        "opis": "Wstrząsająca relacja: Niedźwiedź ruszył na człowieka na własnym podwórku!",
        "link": "https://esanok.pl/2026/niedzwiedz-zaatakowal-w-garazu-ruszył-za-mna-w-poscig-video.html"
    },
    {
        "data": "12.05.2026",
        "miejsce": "Tarnawa Górna",
        "coords": [49.4960, 22.2640],
        "opis": "Niedźwiedź spacerował pod samymi oknami domów.",
        "link": "https://esanok.pl/2026/niedzwiedz-spacerowal-pod-samymi-oknami-w-tarnawie-gornej-video.html"
    }
]

# 3. INTERFEJS
st.title("🐻 BearAlert PRO: Monitoring Bieszczady")
st.info("Dane wprowadzane ręcznie przez operatora - brak opóźnień i blokad.")

col_map, col_list = st.columns([2, 1])

with col_map:
    # Mapa ustawiona centralnie na Bieszczady
    m = folium.Map(location=[49.45, 22.35], zoom_start=10, tiles='CartoDB dark_matter')
    
    for p in incydenty:
        html = f"""
        <div style="font-family: Arial; color: black; min-width: 180px;">
            <h4 style="margin:0; color:red;">{p['miejsce']}</h4>
            <p style="font-size:12px; margin:5px 0;"><b>Data: {p['data']}</b></p>
            <p style="font-size:11px;">{p['opis']}</p>
            <a href="{p['link']}" target="_blank" style="color:blue;">Otwórz artykuł</a>
        </div>
        """
        folium.Marker(
            location=p['coords'],
            popup=folium.Popup(html, max_width=250),
            tooltip=f"{p['miejsce']} - {p['data']}",
            icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
        ).add_to(m)
    
    st_folium(m, width="100%", height=550, key="mapa_reczna")

with col_list:
    st.metric("Aktywne alerty", len(incydenty))
    st.divider()
    st.subheader("🚩 Ostatnie zdarzenia")
    for p in incydenty:
        with st.expander(f"📍 {p['miejsce']} ({p['data']})"):
            st.write(p['opis'])
            st.link_button("Szczegóły", p['link'])

st.caption("Aby dodać nowy punkt: Edytuj listę 'incydenty' w kodzie aplikacji.")
