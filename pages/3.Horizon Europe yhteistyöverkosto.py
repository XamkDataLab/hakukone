import streamlit as st
import pandas as pd
import networkx as nx
import textwrap
import json  
from pyvis.network import Network
import streamlit.components.v1 as components
from queries import fetch_collaboration_data

data = fetch_collaboration_data()

def create_graph(data):
    G = nx.Graph()
    for idx, row in data.iterrows():
        project_title = row['ProjectTitle']
        split_title = textwrap.fill(project_title, width=30)
        hover_text = (
            f"ProjectId: {row['ProjectId']}\n"
            f"ProjectTitle: {split_title}\n"
            f"FinnishOrgContribution: {row['FinnishOrgContribution']}\n"
            f"ProjectRole: {row['ProjectRole']}\n"
            f"StartDate: {row['StartDate']}\n"
            f"EndDate: {row['EndDate']}"
        )
        G.add_node(row['FinnishOrgName'], color='red', title=hover_text)  
        G.add_node(row['CollaboratorOrgName'], color='blue') 
        G.add_edge(row['FinnishOrgName'], row['CollaboratorOrgName'], title=row['euroSciVocTitle'], country=row['CollaboratorCountry'])
    return G

def filter_data(data, title=None, country=None, finnish_org=None):
    filtered_data = data.copy()
    if title and title != 'None':
        filtered_data = filtered_data[filtered_data['euroSciVocTitle'] == title]
    if country and country != 'None':
        filtered_data = filtered_data[filtered_data['CollaboratorCountry'] == country]
    if finnish_org and finnish_org != 'None':
        filtered_data = filtered_data[filtered_data['FinnishOrgName'] == finnish_org]
    return filtered_data

def visualize_graph(graph, gravitational_constant, central_gravity):
    if graph.number_of_edges() > 0:
        nt = Network(notebook=False, height="500px", width="100%")
        
        for node, attr in graph.nodes(data=True):
            nt.add_node(node, color=attr.get('color', 'blue'), title=attr.get('title', ''))
        
        for u, v, attr in graph.edges(data=True):
            nt.add_edge(u, v)
        
        physics_options = {
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": gravitational_constant,
                    "centralGravity": central_gravity,
                    "springLength": 100,
                    "springConstant": 0.05,
                    "damping": 0.1,
                    "avoidOverlap": 0.1
                },
                "maxVelocity": 50,
                "minVelocity": 0.1,
                "solver": "barnesHut",
                "stabilization": {
                    "enabled": True,
                    "iterations": 1000,
                    "updateInterval": 25,
                    "onlyDynamicEdges": False,
                    "fit": True
                },
                "timestep": 0.3,
                "adaptiveTimestep": True
            }
        }
        nt.set_options(json.dumps(physics_options))  # Convert to JSON string
        
        nt.save_graph("network.html")
        with open("network.html", "r", encoding="utf-8") as f:
            html = f.read()
        components.html(html, height=500)
    else:
        st.warning("No edges to display. Please select different filters.")

# Streamlit app
st.title('Horizon Europe Suomen yhteistyöverkosto')
st.text('Projektit joissa vähintään yksi osallistuja on suomesta') 

title = st.selectbox('Filter by Field', ['None'] + list(data['euroSciVocTitle'].unique()))
filtered_data = filter_data(data, title=title)

finnish_org = st.selectbox('Filter by Organization', ['None'] + list(filtered_data['FinnishOrgName'].unique()))
filtered_data = filter_data(filtered_data, title=title, finnish_org=finnish_org)

country = st.selectbox('Filter by Country', ['None'] + list(filtered_data['CollaboratorCountry'].unique()))
filtered_data = filter_data(filtered_data, title=title, finnish_org=finnish_org, country=country)

gravitational_constant = st.slider('Gravitational Constant', min_value=-10000, max_value=0, value=-8000, step=100)
central_gravity = st.slider('Central Gravity', min_value=0.0, max_value=1.0, value=0.3, step=0.1)

if title != 'None' or country != 'None' or finnish_org != 'None':
    filtered_graph = create_graph(filtered_data)
    visualize_graph(filtered_graph, gravitational_constant, central_gravity)
else:
    st.warning('Valitse suodatin luodaksesi kaavion')
