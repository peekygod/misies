import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import re

st.set_page_config(page_title="BearAlert: Monitoring Bieszczady", layout="wide", page_icon="🐻")

# Inicjalizacja geokodera
geolocator = Nominatim(user_agent="bieszczady_bear_alert_v2")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

st.title("🐻 BearAlert: esanok.pl LIVE")
st.markdown("Automatyczny system wykrywania zagrożeń na podstawie komunikatów lokalnych.")

# Słowa kluczowe wskazujące na realne zagrożenie (z Twoich screenów)
DANGER_KEYWORDS = ["ataki", "ruszył", "widziany", "spacerował", "posesji", "oknami", "ostrzegają", "niedźwiedzica", "mieszkańca"]

def wyciagnij_miejsce(tekst):
    """
    Zaawansowana próba wyciągnięcia miejscowości i szczegółów z tekstu.
    Szuka wzorców: 'w Zahutyniu', 'w Wołkowyi', 'w miejscowości X'.
    """
    # Usuwamy znaki interpunkcyjne
    czysty_tekst = re.sub(r'[^\w\s]', '', tekst)
    
    # 1. Szukamy frazy "w [Miejscowość]" lub "w miejscowości [Miejscowość]"
    match = re.search(r'(?:w|miejscowości)\s+([A-Z][a-zśćńółężź]+)', tekst)
    if match:
        miejscowosc = match.group(1)
        # Poprawka deklinacji (bardzo uproszczona dla regionu)
        miejscowosc = miejscowosc.replace("Zahutyniu", "Zahutyń").replace("Wołkowyi", "Wołkowyja").replace("Tarnawie", "Tarnawa").replace("Bereźnicy", "Bereźnica")
        return miejscowosc
    return None

def pobierz_dane():
    url = "https://esanok.pl/?s=niedźwiedź"
    headers = {'User-Agent': 'Mozilla/5.0'}
    znaleziska = []
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pobieramy najświeższe artykuły
        artykuly = soup.find_all('article')[:8]
        
        for art in artykuly:
            tytul_elem = art.find('h2', class_='entry-title')
            if not tytul_elem: continue
            
            tytul = tytul_elem.text.strip()
            link = tytul_elem.find('a')['href']
            
            # Pobieramy wstęp (summary)
            summary_elem = art.find('div', class_='entry-summary')
            summary = summary_elem.text.strip() if summary_elem else ""
            
            # Czy to artykuł o niedźwiedziu z Twojej "czarnej listy"?
            pelny_tekst = (tytul + " " + summary).lower()
            
            if "niedźwiedź" in pelny_tekst or "niedźwiedzica" in pelny_tekst:
                if any(k in pelny_tekst for k in DANGER_KEYWORDS):
                    miejsce = wyciagnij_miejsce(tytul)
                    if not miejsce: # Jeśli nie ma w tytule, szukaj w opisie
                        miejsce = wyciagnij_miejsce(summary)
                    
                    if miejsce:
                        # Geokodowanie - szukamy konkretnie w naszym regionie
                        loc = geocode(f"{miejsce}, Podkarpackie, Polska")
                        coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                        
                        znaleziska.append({
                            "tytul": tytul,
                            "link": link,
                            "miejsce": miejsce,
                            "coords": coords,
                            "opis": summary[:150] + "..."
                        })
        return znaleziska
    except Exception as e:
        return []

# Główna logika aplikacji
if 'data' not in st.session_state:
    with st.spinner('Pobieram najnowsze raporty...'):
        st.session_state.data = pobierz_dane()

# Przyciski kontrolne
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Odśwież"):
        st.session_state.data = pobierz_dane()
        st.rerun()

# MAPA
m = folium.Map(location=[49.460, 22.350], zoom_start=11, tiles="OpenStreetMap")

for item in st.session_state.data:
    # Czerwona pulsująca kropka dla każdego zgłoszenia
    folium.Marker(
        location=item['coords'],
        popup=folium.Popup(f"<b>{item['tytul']}</b><br><a href='{item['link']}' target='_blank'>Link do eSanok</a>", max_width=250),
        tooltip=f"{item['miejsce']}: {item['tytul']}",
        icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
    ).add_to(m)

st_folium(m, width="100%", height=550)

# LISTA PONIŻEJ
st.subheader("⚠️ Ostatnie wykryte incydenty")
if st.session_state.data:
    for n in st.session_state.data:
        with st.container():
            st.error(f"**{n['miejsce']}**: {n['tytul']}")
            st.write(n['opis'])
            st.markdown(f"[Czytaj pełną relację na esanok.pl]({n['link']})")
            st.divider()
else:
    st.success("Brak nowych komunikatów o niedźwiedziach w ostatnim czasie.")
