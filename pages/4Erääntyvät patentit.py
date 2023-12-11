import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from queries import *

def transform_text(text):
    if pd.isna(text):  
        return None
    return ' '.join([word.capitalize() for word in text.split()])

df = fetch_legal_status_data()

df['legal_status_anticipated_term_date'] = pd.to_datetime(df['legal_status_anticipated_term_date'])
df = df[df['legal_status_anticipated_term_date'].notna()]

current_date = datetime.today().strftime('%Y-%m-%d')
st.title(f"Yritysten erääntyviä patentteja {current_date}")
df['Hakija'] = df['yritys'].where(df['yritys'].notna(), df['extracted_name'].apply(transform_text))

option = st.selectbox('Näytä patentit jotka eräänyvät', ['3 kuukauden kuluessa', '6 kuukauden kuluessa', '12 kuukauden kuluessa'])

# Set the date range
min_date = datetime.today()
if option == '3 kuukauden kuluessa':
    max_date = min_date + timedelta(days=90)
elif option == '6 kuukauden kuluessa':
    max_date = min_date + timedelta(days=180)
else:  # 12 kuukauden kuluessa
    max_date = min_date + timedelta(days=365)

expiring_df = df[(df['legal_status_anticipated_term_date'] >= min_date) & (df['legal_status_anticipated_term_date'] <= max_date)]

unique_applicants = expiring_df['Hakija'].dropna().unique().tolist()
#selected_applicant = st.selectbox('Valitse hakija:', unique_applicants)

unique_applicants = [''] + sorted(expiring_df['Hakija'].dropna().unique().tolist())  # Add a blank option at the beginning
selected_applicant = st.selectbox('Valitse hakija:', unique_applicants)

if selected_applicant:  # Only filter by applicant if one is selected
    filtered_df = expiring_df[expiring_df['Hakija'] == selected_applicant]
else:
    filtered_df = expiring_df

filtered_df = expiring_df[expiring_df['Hakija'] == selected_applicant]
filtered_df = filtered_df.rename(columns={"invention_title": "Keksintö"})
filtered_df['legal_status_anticipated_term_date'] = filtered_df['legal_status_anticipated_term_date'].dt.strftime('%Y-%m-%d')
filtered_df = filtered_df.rename(columns={"legal_status_anticipated_term_date": "Erääntymispäivä"})
filtered_df['Link'] = "https://www.lens.org/lens/patent/" + filtered_df['lens_id'].astype(str)
filtered_df['Link'] = '<a href="' + filtered_df['Link'] + '" target="_blank">' + "Link" + '</a>'

st.write(f"Aktiiviset patentit hakijalta {selected_applicant} jotka erääntyvät seuraavan {option}:")

html_table = filtered_df[['publication_type', 'Keksintö', 'Hakija', 'Erääntymispäivä', 'Link']].to_html(escape=False, index=False)
st.markdown(html_table, unsafe_allow_html=True)
