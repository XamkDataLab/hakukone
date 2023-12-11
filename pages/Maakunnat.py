import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from queries import *

def get_emblem_url_from_github(maakunta_name):
    base_url = "https://raw.githubusercontent.com/XamkDataLab/hakukone/main/vaakunat"
    return f"{base_url}/{maakunta_name}.svg"

df = fetch_aggregated_data()
df = df[df['Maakunnan_nimi'].notna()]
#st.dataframe(df)
maakunnan_nimi_list = df['Maakunnan_nimi'].unique().tolist()
maakunnan_nimi_list.insert(0, "All")  
#st.dataframe(df)
# Create a placeholder for the emblem at the top
emblem_placeholder = st.empty()

# Display the maakunta selectbox
selected_maakunnan_nimi = st.selectbox('Select Maakunnan_nimi:', maakunnan_nimi_list)

# If a specific maakunta is selected, display the emblem at the placeholder's position
if selected_maakunnan_nimi != "All":
    emblem_url = get_emblem_url_from_github(selected_maakunnan_nimi)
    emblem_placeholder.image(emblem_url, width=100)

# Funding sources for the Sankey diagram
sources = ['Total_Funding', 'Total_EU_Horizon_Funding', 'Total_Business_Finland_Funding', 'Total_Tutkimusrahoitus']
selected_source = st.selectbox('Select Source:', ["All"] + sources)

if selected_maakunnan_nimi == "All":


    
    maakunta_values = df['Maakunnan_nimi'].unique().tolist()

    # Filter by the selected source if it's not "All"
    if selected_source != "All":
        sources = [selected_source]

    # Create lists to store Sankey diagram data
    source_indices = []
    target_indices = []
    values = []

    # Populate the lists with data
    for idx, source in enumerate(sources):
        grouped = df.groupby('Maakunnan_nimi')[source].sum()
        for maakunta_idx, maakunta in enumerate(maakunta_values):
            source_indices.append(idx)
            target_indices.append(len(sources) + maakunta_idx)
            values.append(grouped[maakunta])

    # Create the Sankey diagram
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
    
    # Display the Sankey diagram in Streamlit
    st.plotly_chart(fig)
    st.dataframe(df[['y_tunnus', 'yritys']])

else:
    
    filtered_df = df[df['Maakunnan_nimi'] == selected_maakunnan_nimi]

    # Replace None values with "unknown" in 'yhtiömuoto'
    filtered_df['yhtiömuoto'].fillna('unknown', inplace=True)

    yhtiömuoto_values = filtered_df['yhtiömuoto'].unique().tolist()

    # Filter by the selected source if it's not "All"
    if selected_source != "All":
        sources = [selected_source]

    # Prepare data for the Sankey diagram
    source_indices = []
    target_indices = []
    values = []

    for idx, source in enumerate(sources):
        grouped = filtered_df.groupby('yhtiömuoto')[source].sum()
        for yhtiömuoto_idx, yhtiömuoto in enumerate(yhtiömuoto_values):
            source_indices.append(idx)
            target_indices.append(len(sources) + yhtiömuoto_idx)
            values.append(grouped[yhtiömuoto])

    # Create the Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=sources + yhtiömuoto_values
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values
        )
    ))
    
    # Display the Sankey diagram in Streamlit
    st.plotly_chart(fig)
    st.dataframe(filtered_df)
    st.dataframe(filtered_df[['y_tunnus', 'yritys', 'yrityksen_rekisteröimispäivä', 'Maakunnan_nimi', 'Total_Business_Finland_Funding', 'Patent_Applications_Count', 'Total_Funding', 'Total_EU_Horizon_Funding', 'Total_Tutkimusrahoitus']])
