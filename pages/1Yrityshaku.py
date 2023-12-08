import streamlit as st
from queries import *
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

if st.button("Clear All"):
    # Clear values from *all* all in-memory and on-disk data caches:
    # i.e. clear values from both square and cube
    st.cache_data.clear()
    
small_font_style = """
<style>
    .small-font {
        font-size: 8px;
    }
</style>
"""
medium_font_style = """
<style>
    .medium-font {
        font-size: 12px;
        font-weight: bold;
    }
</style>
"""

large_font_style = """
<style>
    .large-font {
        font-size: 19px;
    }
</style>
"""

large_number_style = """
<style>
    .large-number {
        font-size: 16px;   
    }
</style>
"""

st.markdown(small_font_style, unsafe_allow_html=True)
st.markdown(medium_font_style, unsafe_allow_html=True)
st.markdown(large_font_style, unsafe_allow_html=True)
st.markdown(large_number_style, unsafe_allow_html=True)

st.title('Hae yrityksen tiedot')

# Input for Y_tunnus
y_tunnus = st.text_input("Anna Y-tunnus (ja paina enter)")
st.session_state['y_tunnus'] = y_tunnus

def create_bar_chart(data, column, title, xaxis_title):
    # Compute value counts and reset index
    counts = data[column].value_counts().reset_index()

    # Rename the columns for clarity
    counts.columns = [xaxis_title, 'Frequency']

    # Sort the dataframe so that the highest frequency is at the bottom (for horizontal bar chart)
    counts.sort_values(by='Frequency', ascending=True, inplace=True)

    # Create the bar chart with descriptions on y-axis and frequencies on x-axis
    fig = px.bar(counts, y=xaxis_title, x='Frequency', orientation='h')

    # Update layout: remove axis labels
    fig.update_layout(
        title=title,
        xaxis_title='',  # Removing x-axis label
        yaxis_title='',  # Removing y-axis label
        template='plotly_white',
        hoverlabel=dict(font_size=16)  # Enlarge hover label font size
    )

    # Update hover information
    fig.update_traces(hovertemplate='%{y}: %{x}<extra></extra>')

    return fig


def format_currency(number):
    return f"{number:,.0f} €".replace(",", " ")
    
def plot_time_series(df, title, date_col, money_cols):
    # Convert date column to just the year part
    df['year'] = df[date_col].dt.year

    # Group by year and sum the money columns
    df_grouped = df.groupby('year')[money_cols].sum().reset_index()

    # Create a Plotly figure
    fig = px.line(df_grouped, x='year', y=money_cols, title=title)

    # Customize the layout if needed
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Funding',
        legend_title='Funding Type'
    )

    return fig
    
def breakdown_cpc(code):
    section = code[0]
    c_class = code[:3]
    subclass = code[:4]
    group = code.split('/')[0]
    subgroup = code
    return pd.Series([section, c_class, subclass, group, subgroup])
    
json_url = "https://raw.githubusercontent.com/XamkDataLab/strmlit/main/cpc_ultimate_titles.json"

def make_cpc(df):
    
    cpc = pd.read_json(json_url)
    df[['Section', 'Class', 'Subclass', 'Group', 'Subgroup']] = df['cpc_classification'].apply(breakdown_cpc)
    df['Group'] = df['Group'].apply(lambda x: x + "/00")
    #df.drop(['cpc_code_split', 'class'], axis=1, inplace=True)
    df['Section Description'] = df['Section'].map(cpc.set_index('Code')['Description'])
    df['Class Description'] = df['Class'].map(cpc.set_index('Code')['Description'])
    df['Subclass Description'] = df['Subclass'].map(cpc.set_index('Code')['Description'])
    df['Group Description'] = df['Group'].map(cpc.set_index('Code')['Description'])
    df['Subgroup Description'] = df['Subgroup'].map(cpc.set_index('Code')['Description'])
    return df

    fig = go.Figure()

    for money_col in money_cols:
        fig.add_trace(go.Scatter(x=df_grouped['year'], y=df_grouped[money_col], mode='lines', name=money_col))

    fig.update_layout(title=title, xaxis_title='Year', yaxis_title='Money', hovermode='closest')

    return fig

if y_tunnus:
    data = fetch_data2(y_tunnus)
    if not data.empty:
        st.markdown(f"<div class='large-font'>{data['yritys'].iloc[0]}</div>", unsafe_allow_html=True)
        yritys_basename = data['yritys_basename2'].iloc[0]
        st.session_state['yritys_basename2'] = yritys_basename
        ynimi = data['yritys'].iloc[0]
        st.session_state['yritys'] = ynimi

        col1, col2, col3 = st.columns(3)  # Create three columns

        # Content for the first column
        card_content1 = f"""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
        <div class="medium-font">EU rahoitus 2013-2030</div>
        <div class="large-number">{format_currency(int(data['Total_EU_Horizon_Funding'].iloc[0]))}</div>
        <hr>
        <div class="medium-font">EURA-rahoitus 2014-2020 ohjelmakausi</div>
        <div class="large-number">{format_currency(int(data['Total_Funding'].iloc[0]))}</div>
        <hr>
        <div class="medium-font">EURA-rahoitus 2021-2027 ohjelmakausi</div>
        <div class="large-number">{format_currency(int(data['Total_EURA2027_planned_funding'].iloc[0]))}</div>
        </div>
        """
        col1.markdown(card_content1, unsafe_allow_html=True)

        # Content for the second column
        card_content2 = f"""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
        <div class="medium-font">Patenttidokumenttien määrä</div>
        <div class="large-number">{int(data['Patent_Applications_Count'].iloc[0]):,}</div>
        <hr>
        <div class="medium-font">Tavaramerkkien määrä</div>
        <div class="large-number">{int(data['Trademarks_Count'].iloc[0]):,}</div>
        </div>
        """
        col2.markdown(card_content2, unsafe_allow_html=True)

        # Content for the third column
        card_content3 = f"""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
        <div class="medium-font">Business Finland avustukset</div>
        <div class="large-number">{format_currency(int(data['Total_Business_Finland_Funding'].iloc[0]))}</div>
        <hr>
        <div class="medium-font">Business Finland tutkimusrahoitus</div>
        <div class="large-number">{int(data['Total_Tutkimusrahoitus'].iloc[0]):,}</div>
        </div>
        """
        col3.markdown(card_content3, unsafe_allow_html=True)
    else:
        st.write("Dataa ei löytynyt :(")

    if y_tunnus:
        patents_df, trademarks_df = fetch_time_series_data(y_tunnus)

        patents_df['year'] = patents_df['date_published'].dt.year if not patents_df.empty else pd.Series(dtype=int)
        trademarks_df['year'] = trademarks_df['applicationDate'].dt.year if not trademarks_df.empty else pd.Series(dtype=int)

        patents_by_year = patents_df.groupby('year').size().reset_index(name='Patents') if not patents_df.empty else pd.DataFrame({'year':[], 'Patents':[]})
        trademarks_by_year = trademarks_df.groupby('year').size().reset_index(name='Trademarks') if not trademarks_df.empty else pd.DataFrame({'year':[], 'Trademarks':[]})

        combined_years = set(patents_by_year['year']).union(set(trademarks_by_year['year']))
        combined_df = pd.DataFrame({'year': list(combined_years)}).merge(patents_by_year, on='year', how='outer').merge(trademarks_by_year, on='year', how='outer').fillna(0)

        if not combined_df.empty:
            fig = px.bar(
                combined_df,
                x='year',
                y=['Patents', 'Trademarks'],
                barmode='group',
                title='Patenttidokumenttien ja tavaramerkkien määrä'
            )
            st.plotly_chart(fig)
        else:
            st.write("No data available for the provided Y-Tunnus.")

    if y_tunnus:
        EURA_df, BF_df, EURA2_df, EUmuu_df = fetch_time_series_data_funding(y_tunnus)

        BF_df['Myöntämisvuosi'] = pd.to_datetime(BF_df['Myöntämisvuosi'], format='%Y', errors='coerce')
        EURA2_df['Start_date'] = pd.to_datetime(EURA2_df['Start_date'], errors='coerce')
        EUmuu_df['Year'] = pd.to_datetime(EUmuu_df['Year'], format='%Y', errors='coerce')
        EURA_df['Aloituspvm'] = pd.to_datetime(EURA_df['Aloituspvm'], errors='coerce')
        
        dataframes = {
            'EURA2020': EURA_df,
            'Business Finland': BF_df,
            'EURA2027': EURA2_df,
            'EU other': EUmuu_df
        }

        selected_df_name = st.selectbox('Select the dataframe:', list(dataframes.keys()))

        df = dataframes[selected_df_name].copy()

        date_col = None
        money_cols = []
        if selected_df_name == 'Business Finland':
            date_col = 'Myöntämisvuosi'
            money_cols = ['Tutkimusrahoitus', 'Avustus']
        elif selected_df_name == 'EURA2027':
            date_col = 'Start_date'
            money_cols = ['Planned_EU_and_state_funding']
        elif selected_df_name == 'EU other':
            date_col = 'Year'
            money_cols = ['Beneficiary’s contracted amount (EUR)']
        elif selected_df_name == 'EURA2020':
            date_col = 'Aloituspvm'
            money_cols = ['Toteutunut_EU_ja_valtion_rahoitus']

        if date_col and money_cols:
            fig = plot_time_series(df, f'Time-Series for {selected_df_name}', date_col, money_cols)
            st.plotly_chart(fig)
        else:
            st.error("Error: Date or money columns not set correctly.")
    
    
    if y_tunnus:
        cpc_data = fetch_company_cpc_data(y_tunnus)
        cpc_class_mapping = {
        'A': 'HUMAN NECESSITIES',
        'B': 'PERFORMING OPERATIONS; TRANSPORTING',
        'C': 'CHEMISTRY; METALLURGY',
        'D': 'TEXTILES; PAPER',
        'E': 'FIXED CONSTRUCTIONS',
        'F': 'MECHANICAL ENGINEERING; LIGHTING; HEATING; WEAPONS; BLASTING',
        'G': 'PHYSICS',
        'H': 'ELECTRICITY',
        'Y': 'GENERAL TAGGING OF NEW TECHNOLOGICAL DEVELOPMENTS'
        }
    
        cpc_data['cpc_class'] = cpc_data['cpc_code'].str[0].map(cpc_class_mapping)
        cpc_class_counts = cpc_data['cpc_class'].value_counts()

        # Create a bar chart using Plotly
        fig = px.bar(cpc_class_counts, 
                     x=cpc_class_counts.index, 
                     y=cpc_class_counts.values,
                     labels={'x': 'CPC Patent Section', 'y': 'Number of Classifications'},
                     title='Distribution of Patents Across CPC Sections')
        
        # In a Streamlit app, use st.plotly_chart() to display the plot
        st.plotly_chart(fig)
        st.dataframe(cpc_data)
        cpc_data = cpc_data[cpc_data['cpc_classification'].notna() & cpc_data['cpc_classification'].apply(lambda x: isinstance(x, str))]

        cpc_data2 = make_cpc(cpc_data)
        st.dataframe(cpc_data2)
    
        fig_class = create_bar_chart(cpc_data2, 'Class Description', 'Frequency of Class Descriptions', 'Class Description')
        fig_subclass = create_bar_chart(cpc_data2, 'Subclass Description', 'Frequency of Subclass Descriptions', 'Subclass Description')
        
        # Streamlit application
        st.title('Patenttien luokitukset')
        
        st.write("## Luokkien kuvaukset")
        st.plotly_chart(fig_class)
        
        st.write("## Alaluokkien kuvaukset")
        st.plotly_chart(fig_subclass)
        
            
        
         
                
