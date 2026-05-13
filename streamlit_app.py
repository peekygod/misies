import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="BearAlert Bieszczady", layout="wide")

st.title("🐻 BearAlert: Lesko - Solina - Bieszczady")
st.info("System ostrzegania przed aktywnością niedźwiedzi.")

# Twoje dane (Lesko, Zagórz, Solina, Myczków, Zahutyn, Załuż)
if 'incydenty' not in st.session_state:
    st.session_state.incydenty = [
        {"miasto": "Lesko", "lat": 49.470, "lon": 22.330, "status": "Wysoki", "info": "Widziany przy ogródkach."},
        {"miasto": "Zagórz", "lat": 49.508, "lon": 22.272, "status": "Średni", "info": "Ślady nad Osławą."},
        {"miasto": "Zahutyn", "lat": 49.525, "lon": 22.245, "status": "Wysoki", "info": "Pojawia się wieczorami pod lasem."},
        {"miasto": "Myczków", "lat": 49.415, "lon": 22.410, "status": "Krytyczny", "info": "Niedźwiedzica z młodymi - UWAGA!"},
        {"miasto": "Solina", "lat": 49.395, "lon": 22.450, "status": "Średni", "info": "Okolice ścieżek spacerowych."}
    ]

# Mapa
m = folium.Map(location=[49.460, 22.350], zoom_start=12)

for i in st.session_state.incydenty:
    kolor = "red" if i['status'] in ["Wysoki", "Krytyczny"] else "orange"
    folium.Circle(location=[i['lat'], i['lon']], radius=1200, color=kolor, fill=True, fill_opacity=0.3).add_to(m)
    folium.Marker([i['lat'], i['lon']], popup=i['info'], tooltip=i['miasto']).add_to(m)

st_folium(m, width="100%", height=500)

st.write("### 📋 Ostatnie meldunki:")
for inc in reversed(st.session_state.incydenty):
    st.warning(f"**{inc['miasto']}** - {inc['info']}")
  
