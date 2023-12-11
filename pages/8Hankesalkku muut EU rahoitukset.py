import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from queries import *

def truncate_text(text, max_length):
    return text if len(text) <= max_length else text[:max_length] + "..."

def generate_project_viz(df, filter_ended=True):
    df['Project start date'] = pd.to_datetime(df['Project start date'], errors='coerce')
    df['Project end date'] = pd.to_datetime(df['Project end date'], errors='coerce')

    if filter_ended:
        today = pd.Timestamp(datetime.date.today())
        df = df[df['Project end date'] > today]

    max_length = 60
    df['Truncated Name'] = df['Subject of grant or contract'].apply(lambda x: truncate_text(x, max_length))
    df['Hover Info'] = 'Budget: ' + df['Beneficiary’s contracted amount (EUR)'].astype(str)

    fig = px.timeline(df, x_start="Project start date", x_end="Project end date", y="Truncated Name", 
                      color="Truncated Name", 
                      hover_name="Subject of grant or contract", 
                      hover_data=["Hover Info"], 
                      title="Hankkeet")

    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(marker_line_width=df['Beneficiary’s contracted amount (EUR)']/500000)
    fig.update_layout(showlegend=False)
    fig.update_layout(yaxis_title_text="")

    st.plotly_chart(fig)

# Retrieve values from session state
y_tunnus = st.session_state.get('y_tunnus')
yritys_basename = st.session_state.get('yritys_basename2')

if yritys_basename and y_tunnus:
    st.title(f"EU muu rahoitus yritykselle {yritys_basename}")
    data = fetch_horizon_data(y_tunnus)

    programme_options = ["All"] + sorted(data["Programme name"].unique().tolist())
    selected_programme = st.selectbox("Select Programme", programme_options)

    if selected_programme != "All":
        data = data[data["Programme name"] == selected_programme]

    if 'filter_ended' not in st.session_state:
        st.session_state.filter_ended = False

    if st.button("Piilota loppuneet projektit" if not st.session_state.filter_ended else "Näytä loppuneet projektit"):
        st.session_state.filter_ended = not st.session_state.filter_ended

    if not data.empty:
        generate_project_viz(data, st.session_state.filter_ended)
    else:
        st.write("No data found.")
else:
    st.header("Anna Y-tunnus yrityshakuun!")
