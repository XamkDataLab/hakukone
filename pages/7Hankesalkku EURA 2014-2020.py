import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from queries import *

def truncate_text(text, max_length):
    return text if len(text) <= max_length else text[:max_length] + "..."

def generate_eura_project_viz(df, filter_ended=True):
    df['Aloituspvm'] = pd.to_datetime(df['Aloituspvm'])
    df['Päättymispvm'] = pd.to_datetime(df['Päättymispvm'])

    if filter_ended:
        today = pd.Timestamp(datetime.date.today())
        df = df[df['Päättymispvm'] > today]

    max_length = 60
    df['Truncated Name'] = df['Hankkeen_nimi'].apply(lambda x: truncate_text(x, max_length))
    df['Hover Info'] = 'Budget: ' + df['Myönnetty_EU_ja_valtion_rahoitus'].astype(str)

    fig = px.timeline(df, x_start="Aloituspvm", x_end="Päättymispvm", y="Truncated Name",
                      color="Truncated Name",
                      hover_name="Hankkeen_nimi",
                      hover_data=["Hover Info"],
                      title="EURA2020 Projects")
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(marker_line_width=df['Myönnetty_EU_ja_valtion_rahoitus']/500000)
    fig.update_layout(showlegend=False)
    fig.update_layout(yaxis_title_text="")

    st.plotly_chart(fig)

# Retrieve the yritys_basename from session state
y_tunnus = st.session_state.get('y_tunnus')
yritys_basename = st.session_state.get('yritys_basename2')

if y_tunnus and yritys_basename:
    st.title(f"EURA rahoitus yritykselle {yritys_basename}")
    data = fetch_eura_data(y_tunnus)
else:
    st.write("Invalid or missing parameters.")
    data = pd.DataFrame()

if not data.empty:
    toimintalinja_options = ["All"] + sorted(data["Toimintalinja"].unique().tolist())
    selected_toimintalinja = st.selectbox("Valitse toimintalinja", toimintalinja_options)

    if selected_toimintalinja != "All":
        data = data[data["Toimintalinja"] == selected_toimintalinja]

    if 'filter_ended' not in st.session_state:
        st.session_state.filter_ended = False

    if st.button("Piilota loppuneet projektit" if not st.session_state.filter_ended else "Näytä loppuneet projektit"):
        st.session_state.filter_ended = not st.session_state.filter_ended

    generate_eura_project_viz(data, st.session_state.filter_ended)
else:
    st.write("No data found.")
