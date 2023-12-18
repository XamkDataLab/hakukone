import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from queries import *

def get_emblem_url_from_github(maakunta_name):
    base_url = "https://raw.githubusercontent.com/XamkDataLab/hakukone/main/vaakunat"
    return f"{base_url}/{maakunta_name}.svg"

def plot_top_patents(df):
    top_patents_df = df.sort_values(by='Patent_Applications_Count', ascending=False).head(10)
    fig_patents = go.Figure(data=[
        go.Bar(x=top_patents_df['yritys'], y=top_patents_df['Patent_Applications_Count'],
               text=top_patents_df['Patent_Applications_Count'], textposition='auto')
    ])
    fig_patents.update_layout(title='Top 10 Yritykset joilla eniten patenttidokumentteja',
                              xaxis_title='Yritys',
                              yaxis_title='Patenttidokumenttien määrä')
    return fig_patents

def plot_top_trademarks(df):
    top_trademarks_df = df.sort_values(by='Trademarks_Count', ascending=False).head(10)
    fig_trademarks = go.Figure(data=[
        go.Bar(x=top_trademarks_df['yritys'], y=top_trademarks_df['Trademarks_Count'],
               text=top_trademarks_df['Trademarks_Count'], textposition='auto')
    ])
    fig_trademarks.update_layout(title='Top 10 Yritykset joilla eniten tavaramerkkejä',
                                 xaxis_title='Yritys',
                                 yaxis_title='Tavaramerkkien määrä')
    return fig_trademarks

def plot_top_funding(df, funding_column):
    # Filter out companies with zero funding
    df_with_funding = df[df[funding_column] > 0]

    # Sort and limit to top 10, if more than 10 companies have funding
    top_funding_df = df_with_funding.sort_values(by=funding_column, ascending=True)
    if len(top_funding_df) > 10:
        top_funding_df = top_funding_df.tail(10)

    # Check if there are any companies with funding
    if top_funding_df.empty:
        return None

    fig_funding = go.Figure(data=[
        go.Bar(y=top_funding_df['yritys'], x=top_funding_df[funding_column], orientation='h',
               text=top_funding_df[funding_column], textposition='auto')
    ])
    fig_funding.update_layout(title=f'Top {len(top_funding_df)} Yritykset joilla eniten {funding_column} - {selected_maakunnan_nimi}',
                              yaxis_title='Yritys',
                              xaxis_title='Rahoituksen määrä')
    return fig_funding



st.header("Maakunnat")
df = fetch_aggregated_data()
df = df.rename(columns={
    "Total_Funding": "EURA2014-2020 rahoitus",
    "Total_Horizon_Europe_Funding": "Horizon Europe rahoitus",
    "Total_EURA2027_Funding": "EURA2021-2027 rahoitus",
    "Total_Business_Finland_Funding": "Business Finland avustukset",
    "Total_Tutkimusrahoitus": "Business Finland tutkimusrahoitus"
})
df = df[df['Maakunnan_nimi'].notna()]
maakunnan_nimi_list = df['Maakunnan_nimi'].unique().tolist()
maakunnan_nimi_list.insert(0, "All")

emblem_placeholder = st.empty()

selected_maakunnan_nimi = st.selectbox('Valitse maakunta', maakunnan_nimi_list)

if selected_maakunnan_nimi != "All":
    emblem_url = get_emblem_url_from_github(selected_maakunnan_nimi)
    emblem_placeholder.image(emblem_url, width=100)

if selected_maakunnan_nimi == "All":
    sources = ['EURA2014-2020 rahoitus', 'Horizon Europe rahoitus', 'EURA2021-2027 rahoitus', 'Business Finland avustukset', 'Business Finland tutkimusrahoitus']
    selected_source = st.selectbox('Valitse rahoituslähde', ["All"] + sources)

if selected_maakunnan_nimi == "All":
    maakunta_values = df['Maakunnan_nimi'].unique().tolist()

    if selected_source != "All":
        sources = [selected_source]

    source_indices = []
    target_indices = []
    values = []

    for idx, source in enumerate(sources):
        grouped = df.groupby('Maakunnan_nimi')[source].sum()
        for maakunta_idx, maakunta in enumerate(maakunta_values):
            source_indices.append(idx)
            target_indices.append(len(sources) + maakunta_idx)
            values.append(grouped[maakunta])

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=sources + maakunta_values
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values
        )
    ))
    fig.update_layout(
    title_text='Rahoituksen jakautuminen maakunnittain',
    title_font_size=24
    )
    st.plotly_chart(fig)
    
else:
    filtered_df = df[df['Maakunnan_nimi'] == selected_maakunnan_nimi]
    filtered_df['yhtiömuoto'].fillna('unknown', inplace=True)

    fig_patents = plot_top_patents(filtered_df)
    fig_trademarks = plot_top_trademarks(filtered_df)
    st.plotly_chart(fig_patents)
    st.plotly_chart(fig_trademarks)
    funding_columns = ['EURA2021-2027 rahoitus', 'Horizon Europe rahoitus', 'Business Finland avustukset', 'Business Finland tutkimusrahoitus', 'EURA2014-2020 rahoitus']
    for funding_column in funding_columns:
        fig_funding = plot_top_funding(filtered_df, funding_column)
        if fig_funding:  # Only plot if there are companies with funding
            st.plotly_chart(fig_funding)
    
