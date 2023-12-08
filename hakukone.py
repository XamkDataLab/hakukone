import streamlit as st
import urllib.parse

def get_emblem_url_from_github(maakunta_name):
    base_url = "https://raw.githubusercontent.com/XamkDataLab/strmlit/main/vaakunat"
    encoded_maakunta_name = urllib.parse.quote(maakunta_name)
    return f"{base_url}/{encoded_maakunta_name}.svg"

maakunta_names = [
    "Ahvenanmaa",
    "Etelä-Karjala",
    "Etelä-Pohjanmaa",
    "Etelä-Savo",
    "Kainuu",
    "Kanta-Häme",
    "Keski-Pohjanmaa",
    "Keski-Suomi",
    "Kymenlaakso",
    "Lappi",
    "Pirkanmaa",
    "Pohjanmaa",
    "Pohjois-Karjala",
    "Pohjois-Pohjanmaa",
    "Pohjois-Savo",
    "Päijät-Häme",
    "Satakunta",
    "Uusimaa",
    "Varsinais-Suomi"
]

cols = st.columns(len(maakunta_names))
for idx, maakunta_name in enumerate(maakunta_names):
    with cols[idx]:
        emblem_url = get_emblem_url_from_github(maakunta_name)
        st.image(emblem_url, width=50) 


st.title("IPR-Haku")
st.subheader('IPR-haku on osa IPR Suomi -tietopalvelukokonaisuutta')
st.subheader("Maakuntien innovaatiotilastot")
st.write(
    """
    Tämä sivu kerää yhteen tiedot suomalaisten yritysten IPR-omaisuudesta ja rahoituksesta. Sisältää
    seuraavat työkalut:
    """
)
st.markdown("""
- Yrityshaku: hae yrityskohtaiset tiedot ja organisaatioiden hanke- ja patenttisalkut
- Maakuntasivut: tarkastele maakunnan vahvuusaloja ja yritysten innovaatioita 
- Verkosto: tarkastele yhteishankkeita maakuntien välillä
- Erääntyvät patentit :)
""")
