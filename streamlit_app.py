import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from datetime import datetime
import re

# Konfiguracja strony
st.set_page_config(page_title="BearAlert PRO | Monitoring Bieszczady", layout="wide", page_icon="🐻")

# Stylizacja CSS dla efektu "Premium"
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    .stExpander { border: 1px solid #374151; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Inicjalizacja narzędzi
geolocator = Nominatim(user_agent="bieszczady_bear_monitor_v4")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

def wyciagnij_date_i_miejsce(url):
    """Wchodzi w artykuł i wyciąga dokładną datę oraz próbuje znaleźć lokalizację"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Próba wyciągnięcia daty z meta-tagów lub treści
        data_str = "Nieznana"
        date_tag = soup.find('meta', property='article:published_time')
        if date_tag:
            dt = datetime.fromisoformat(date_tag['content'].replace('Z', '+00:00'))
            data_str = dt.strftime("%d.%m.%L %H:%M")
        else:
            # Szukanie tekstu daty na stronie (np. "12-05-2026")
            text_date = soup.find(text=re.compile(r'\d{2}-\d{2}-\d{4}'))
            if text_date: data_str = text_date.strip()

        # Szukanie miejscowości w treści
        tresc = soup.find('div', class_='entry-content').text if soup.find('div', class_='entry-content') else ""
        miejscowosci = ["Zahutyń", "Wołkowyja", "Tarnawa", "Sanok", "Lesko", "Zagórz", "Solina", "Ustrzyki", "Bereźnica", "Huzele"]
        znaleziona = "Bieszczady"
        for m in miejscowosci:
            if m.lower() in tresc.lower() or m.lower() in url.lower():
                znaleziona = m
                break
                
        return data_str, znaleziona, tresc[:300]
    except:
        return "Brak danych", "Bieszczady", ""

def pobierz_raporty():
    url = "https://esanok.pl/?s=niedźwiedź"
    headers = {'User-Agent': 'Mozilla/5.0'}
    wyniki = []
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        artykuly = soup.find_all('h2', class_='entry-title')[:6] # Ostatnie 6 newsów
        
        for art in artykuly:
            tytul = art.text.strip()
            link = art.find('a')['href']
            
            data_pub, miejsce, opis = wyciagnij_date_i_miejsce(link)
            
            # Geokodowanie
            loc = geocode(f"{miejsce}, Podkarpackie, Polska")
            coords = [loc.latitude, loc.longitude] if loc else [49.46, 22.32]
            
            wyniki.append({
                "Tytuł": tytul,
                "Data": data_pub,
                "Miejsce": miejsce,
                "Link": link,
                "Coords": coords,
                "Opis": opis
            })
        return pd.DataFrame(wyniki)
    except:
        return pd.DataFrame()

# --- SIDEBAR (Statystyki) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/235/235359.png", width=100)
st.sidebar.title("BearAlert Panel")
st.sidebar.info("System skanuje eSanok.pl w poszukiwaniu nowych incydentów.")

if st.sidebar.button("🔄 SZUKAJ NOWYCH ŚLADÓW"):
    st.session_state.df = pobierz_raporty()

if 'df' not in st.session_state:
    st.session_state.df = pobierz_raporty()

df = st.session_state.df

# --- GŁÓWNY PANEL ---
col_map, col_list = st.columns([2, 1])

with col_map:
    st.subheader("📍 Mapa Aktywności (LIVE)")
    # Używamy ciemnego stylu mapy "CartoDB Dark Matter"
    m = folium.Map(location=[49.46, 22.35], zoom_start=11, tiles='CartoDB dark_matter')
    
    if not df.empty:
        for _, row in df.iterrows():
            # Tworzymy ładny dymek HTML
            html = f"""
            <div style="font-family: Arial; color: #333;">
                <h4 style="margin-bottom:5px; color:#e74c3c;">{row['Miejsce']}</h4>
                <p style="font-size:12px;"><b>Data:</b> {row['Data']}</p>
                <p style="font-size:11px;">{row['Tytuł']}</p>
                <a href="{row['Link']}" target="_blank" style="color:#3498db;">Otwórz artykuł</a>
            </div>
            """
            folium.Marker(
                location=row['Coords'],
                popup=folium.Popup(html, max_width=200),
                tooltip=f"{row['Miejsce']} - {row['Data']}",
                icon=folium.Icon(color='red', icon='paw', prefix='fa')
            ).add_to(m)
    
    st_folium(m, width="100%", height=550)

with col_list:
    st.subheader("📊 Statystyki")
    st.metric("Wykryte incydenty", len(df))
    st.metric("Ostatnia aktualizacja", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    st.subheader("📜 Ostatnie wpisy")
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"🔴 {row['Data']} - {row['Miejsce']}"):
                st.write(row['Tytuł'])
                st.caption(row['Opis'] + "...")
                st.link_button("Szczegóły", row['Link'])
    else:
        st.write("Brak danych do wyświetlenia.")

# Stopka
st.markdown("---")
st.caption("Dane pobierane automatycznie z portalu eSanok.pl. Zachowaj ostrożność w lasach!")
