import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import re

st.set_page_config(page_title="BearAlert: Monitoring Bieszczady", layout="wide", page_icon="🐻")

# Inicjalizacja geokodera
geolocator = Nominatim(user_agent="bieszczady_bear_alert_final")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

st.title("🐻 BearAlert: esanok.pl LIVE")

def wyciagnij_miejsce(tekst):
    """Próbuje wyciągnąć miejscowość z odmian używanych przez eSanok"""
    tekst = tekst.replace("Zahutyniu", "Zahutyń").replace("Wołkowyi", "Wołkowyja")
    tekst = tekst.replace("Tarnawie", "Tarnawa").replace("Bereźnicy", "Bereźnica")
    tekst = tekst.replace("Myczkowie", "Myczków").replace("Solinie", "Solina")
    
    # Szukamy słowa po "w " lub "miejscowości "
    match = re.search(r'(?:w|miejscowości)\s+([A-Z][a-zśćńółężź]+)', tekst)
    if match:
        return match.group(1)
    return None

def pobierz_dane_v3():
    # Szukamy bezpośrednio przez wyszukiwarkę esanok
    url = "https://esanok.pl/?s=niedźwiedź"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    znaleziska = []
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukamy wszystkich nagłówków, które mogą być artykułami
        naglowki = soup.find_all(['h1', 'h2', 'h3'])
        
        for n in naglowki:
            tytul = n.text.strip()
            link_elem = n.find('a')
            
            # Jeśli w tytule jest niedźwiedź i mamy link
            if ("niedźwiedź" in tytul.lower() or "niedźwiedzica" in tytul.lower()) and link_elem:
                link = link_elem['href']
                miejsce = wyciagnij_miejsce(tytul)
                
                # Jeśli nie ma miejsca w tytule, dajemy domyślnie Sanok/Bieszczady
                miejsce_do_geokodu = miejsce if miejsce else "Sanok"
                loc = geocode(f"{miejsce_do_geokodu}, Podkarpackie, Polska")
                coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
                
                znaleziska.append({
                    "tytul": tytul,
                    "link": link,
                    "miejsce": miejsce if miejsce else "Bieszczady",
                    "coords": coords
                })
        
        # Usuwamy duplikaty (czasem ten sam link jest w h2 i h3)
        unikalne = {v['link']: v for v in znaleziska}.values()
        return list(unikalne)
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return []

# Pobieranie danych
if 'data' not in st.session_state or st.button("🔄 Odśwież raporty"):
    with st.spinner('Przeszukuję eSanok...'):
        st.session_state.data = pobierz_dane_v3()

# MAPA
m = folium.Map(location=[49.460, 22.350], zoom_start=11)

if st.session_state.data:
    for item in st.session_state.data:
        folium.Marker(
            location=item['coords'],
            popup=f"<b>{item['tytul']}</b><br><a href='{item['link']}'>Czytaj</a>",
            tooltip=f"{item['miejsce']}: {item['tytul']}",
            icon=folium.Icon(color='red', icon='paw', prefix='fa')
        ).add_to(m)
else:
    st.warning("Nie znaleziono aktywnych komunikatów. Sprawdź czy strona esanok.pl działa.")

st_folium(m, width="100%", height=500)

# LISTA DLA PEWNOŚCI
st.subheader("📰 Wszystkie znalezione wzmianki:")
for n in st.session_state.data:
    st.markdown(f"🚩 **{n['miejsce']}**: [{n['tytul']}]({n['link']})")
