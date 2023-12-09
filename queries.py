import pyodbc
import streamlit as st
import pandas as pd

driver = st.secrets["driver"]
server = st.secrets["server"]
database = st.secrets["database"]
username = st.secrets["username"]
password = st.secrets["password"]


def hae_yritysten_summat(y_tunnus):
    # Define the SQL query
    query = """ 
        WITH Funding AS (
        SELECT 
            Y_tunnus,
            SUM(Toteutunut_EU_ja_valtion_rahoitus) as Total_Funding
        FROM 
            eura2020
        WHERE 
            Y_tunnus = ?
        GROUP BY 
            Y_tunnus
    ),
    DesignRights AS (
        SELECT 
            m.applicant_basename,
            COUNT(DISTINCT m.applicationNumber) as Design_Rights_Count
        FROM 
            mallioikeudet m
        JOIN 
            yritykset y ON y.yritys_basename = m.applicant_basename
        WHERE 
            y.y_tunnus = ?
        GROUP BY 
            m.applicant_basename
    ),
    Trademarks AS (
        SELECT 
            t.applicant_basename,
            COUNT(DISTINCT t.applicationNumber) as Trademarks_Count
        FROM 
            tavaramerkit t
        JOIN 
            yritykset y ON y.yritys_basename = t.applicant_basename
        WHERE 
            y.y_tunnus = ?
        GROUP BY 
            t.applicant_basename
    ),
    Patents AS (
        SELECT 
            p.applicant_basename,
            COUNT(DISTINCT p.lens_id) as Patent_Applications_Count
        FROM 
            applicants p
        JOIN 
            yritykset y ON y.yritys_basename2 = p.applicant_basename
        WHERE 
            y.y_tunnus = ?
        GROUP BY 
            p.applicant_basename
    ),
    EUHorizon AS (
        SELECT 
            y_tunnus,
            SUM([Beneficiary’s contracted amount (EUR)]) as Total_EU_Horizon_Funding
        FROM 
            EU_Horizon2
        WHERE 
            y_tunnus = ?
        GROUP BY 
            y_tunnus
    ),
    BusinessFinland AS (
        SELECT 
            Y_tunnus,
            SUM(CAST(Avustus as FLOAT)) as Total_Business_Finland_Funding,
            SUM(CAST(Tutkimusrahoitus as FLOAT)) as Total_Tutkimusrahoitus  -- Sum the Tutkimusrahoitus column
        FROM 
            Business_Finland
        WHERE 
            Y_tunnus = ?
        GROUP BY 
            Y_tunnus
    ),
    EURAuusi AS (
        SELECT 
            Business_ID_of_the_implementing_organisation,
            SUM(Planned_public_funding) as EURA2027_planned_funding
        FROM 
            EURA2027
        WHERE
            Business_ID_of_the_implementing_organisation = ?
        GROUP BY
            Business_ID_of_the_implementing_organisation
    )
            
    SELECT 
        y.y_tunnus,
        y.yritys,
        y.yritys_basename2,
        COALESCE(f.Total_Funding, 0) as Total_Funding,
        COALESCE(d.Design_Rights_Count, 0) as Design_Rights_Count,
        COALESCE(t.Trademarks_Count, 0) as Trademarks_Count,
        COALESCE(p.Patent_Applications_Count, 0) as Patent_Applications_Count,
        COALESCE(eh.Total_EU_Horizon_Funding, 0) as Total_EU_Horizon_Funding,
        COALESCE(bf.Total_Business_Finland_Funding, 0) as Total_Business_Finland_Funding,
        COALESCE(bf.Total_Tutkimusrahoitus, 0) as Total_Tutkimusrahoitus,
        COALESCE(eur.EURA2027_planned_funding,0) as Total_EURA2027_planned_funding
    FROM 
        yritykset y
    LEFT JOIN 
        Funding f ON y.y_tunnus = f.Y_tunnus
    LEFT JOIN 
        DesignRights d ON y.yritys_basename = d.applicant_basename
    LEFT JOIN 
        Trademarks t ON y.yritys_basename = t.applicant_basename
    LEFT JOIN 
        Patents p ON y.yritys_basename2 = p.applicant_basename
    LEFT JOIN 
        EUHorizon eh ON y.y_tunnus = eh.y_tunnus
    LEFT JOIN 
        BusinessFinland bf ON y.y_tunnus = bf.Y_tunnus
    LEFT JOIN
        EURAuusi as eur ON y.y_tunnus = eur.Business_ID_of_the_implementing_organisation
    WHERE 
        y.y_tunnus = ?;
    """
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
           df = pd.read_sql(query, conn, params=(y_tunnus, y_tunnus, y_tunnus, y_tunnus, y_tunnus, y_tunnus, y_tunnus, y_tunnus))
        
    return df
