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

def fetch_time_series_data(y_tunnus):
    patents_query = """
    SELECT y.y_tunnus,
           y.yritys,
           p.date_published,
           p.publication_type,
           p.legal_status_patent_status
    FROM yritykset y
    LEFT JOIN applicants a ON y.yritys_basename2 = a.applicant_basename
    LEFT JOIN patents p ON a.lens_id = p.lens_id
    WHERE y.y_tunnus = ? AND p.date_published IS NOT NULL
    """

    # Trademarks query
    trademarks_query = """
    SELECT y.y_tunnus,
           y.yritys,
           t.applicationDate
    FROM yritykset y
    LEFT JOIN tavaramerkit t ON y.yritys_basename = t.applicant_basename
    WHERE y.y_tunnus = ? AND t.applicationDate IS NOT NULL
    """
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        patents_df = pd.read_sql_query(patents_query, conn, params=(y_tunnus,))
        trademarks_df = pd.read_sql_query(trademarks_query, conn, params=(y_tunnus,))

    return patents_df, trademarks_df

def fetch_company_cpc_data(y_tunnus):
    cpc_query = """
    SELECT DISTINCT y.y_tunnus,
       y.yritys,
       p.lens_id, 
       p.date_published,
       p.publication_type,
       p.legal_status_patent_status,
       invention_title,
       c.cpc_code,
       c.cpc_classification,
       d.class,
       d.title
    FROM yritykset y
    LEFT JOIN applicants a ON y.yritys_basename2 = a.applicant_basename
    LEFT JOIN patents p ON a.lens_id = p.lens_id
    LEFT JOIN cpc_classifications c ON c.lens_id = p.lens_id
    LEFT JOIN cpc_descriptions d ON d.cpc_code = c.cpc_code
    WHERE p.date_published IS NOT NULL AND y.y_tunnus = ?
    """
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        cpc_df = pd.read_sql_query(cpc_query, conn, params=(y_tunnus,))
    return cpc_df

def fetch_time_series_data_funding(y_tunnus):
    EURA_query = """
    SELECT y.y_tunnus,
           y.yritys,
           e1.Aloituspvm,
           e1.Toteutunut_EU_ja_valtion_rahoitus
    FROM yritykset y
    LEFT JOIN EURA2020 e1 ON y.y_tunnus = e1.Y_tunnus
    WHERE y.y_tunnus = ?
    """

    BF_query = """
    SELECT y.y_tunnus,
           y.yritys,
           bf.Myöntämisvuosi,
           bf.Avustus,
           bf.Tutkimusrahoitus
    FROM yritykset y
    LEFT JOIN business_finland bf ON y.y_tunnus = bf.Y_tunnus
    WHERE y.y_tunnus = ?
    
    """
    EURA2_query = """
    SELECT y.y_tunnus,
           y.yritys,
           e2.Start_date,
           e2.Planned_EU_and_state_funding
    FROM yritykset y
    LEFT JOIN EURA2027 e2 ON y.y_tunnus = e2.Business_ID_of_the_implementing_organisation
    WHERE y.y_tunnus = ?
    """

    EUmuu_query = """
    SELECT y.y_tunnus,
           y.yritys,
           e3.Year,
           e3.[Beneficiary’s contracted amount (EUR)]
    FROM yritykset y
    LEFT JOIN EU_Horizon2 e3 ON y.y_tunnus = e3.y_tunnus
    WHERE y.y_tunnus = ?
    """
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        EURA_df = pd.read_sql_query(EURA_query, conn, params=(y_tunnus,))
        BF_df = pd.read_sql_query(BF_query, conn, params=(y_tunnus,))
        EURA2_df = pd.read_sql_query(EURA2_query, conn, params=(y_tunnus,))
        EUmuu_df = pd.read_sql_query(EUmuu_query,conn,params=(y_tunnus,))

    return EURA_df, BF_df, EURA2_df,EUmuu_df

def fetch_aggregated_data():
    query = """
    WITH 
    Funding AS (
        SELECT 
            Y_tunnus,
            SUM(Toteutunut_EU_ja_valtion_rahoitus) as Total_Funding
        FROM 
            eura2020
        GROUP BY 
            Y_tunnus
    ),
    EURA2027Funding AS (
        SELECT 
            Business_ID_of_the_implementing_organisation,
            SUM(Planned_EU_and_state_funding) as Total_EURA2027_Funding
        FROM 
            EURA2027
        GROUP BY 
            Business_ID_of_the_implementing_organisation
    ),
    DesignRights AS (
        SELECT 
            m.applicant_basename,
            COUNT(DISTINCT m.applicationNumber) as Design_Rights_Count
        FROM 
            mallioikeudet m
        JOIN 
            yritykset y ON y.yritys_basename = m.applicant_basename
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
        GROUP BY 
            p.applicant_basename
    ),
    EUHorizon AS (
        SELECT 
            y_tunnus,
            SUM([Beneficiary’s contracted amount (EUR)]) as Total_EU_Horizon_Funding
        FROM 
            EU_Horizon2
        GROUP BY 
            y_tunnus
    ),
    BusinessFinland AS (
        SELECT 
            Business_Finland.Y_tunnus,
            SUM(CAST(Avustus as FLOAT)) as Total_Business_Finland_Funding,
            SUM(CAST(Tutkimusrahoitus as FLOAT)) as Total_Tutkimusrahoitus
        FROM 
            Business_Finland
        JOIN 
            yritykset y on y.y_tunnus = Business_Finland.Y_tunnus
        GROUP BY 
            Business_Finland.Y_tunnus
    ),
    PostinumeroInfo AS (
        SELECT 
            Postinumeroalue,
            Maakunnan_nimi
        FROM 
            Postinumeroalueet
    )
    SELECT 
        y.y_tunnus,
        y.yritys,
        y.yritys_basename2,
        y.postinumero,
        y.yrityksen_rekisteröimispäivä,
        y.toimiala,
        y.päätoimiala,
        y.yhtiömuoto,
        y.status,
        COALESCE(f.Total_Funding, 0) as Total_Funding,
        COALESCE(e27.Total_EURA2027_Funding, 0) as Total_EURA2027_Funding,
        COALESCE(d.Design_Rights_Count, 0) as Design_Rights_Count,
        COALESCE(t.Trademarks_Count, 0) as Trademarks_Count,
        COALESCE(p.Patent_Applications_Count, 0) as Patent_Applications_Count,
        COALESCE(eh.Total_EU_Horizon_Funding, 0) as Total_EU_Horizon_Funding,
        COALESCE(bf.Total_Business_Finland_Funding, 0) as Total_Business_Finland_Funding,
        COALESCE(bf.Total_Tutkimusrahoitus, 0) as Total_Tutkimusrahoitus,
        pi.Maakunnan_nimi
    FROM 
        yritykset y
    LEFT JOIN 
        Funding f ON y.y_tunnus = f.Y_tunnus
    LEFT JOIN 
        EURA2027Funding e27 ON y.y_tunnus = e27.Business_ID_of_the_implementing_organisation
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
        PostinumeroInfo pi ON 
        CASE 
            WHEN RIGHT(y.postinumero, 1) = '1' THEN LEFT(y.postinumero, LEN(y.postinumero) - 1) + '0'
            ELSE y.postinumero
        END 
        = pi.Postinumeroalue
    WHERE 
        COALESCE(f.Total_Funding, 0) <> 0 OR
        COALESCE(e27.Total_EURA2027_Funding, 0) <> 0 OR
        COALESCE(d.Design_Rights_Count, 0) <> 0 OR
        COALESCE(t.Trademarks_Count, 0) <> 0 OR
        COALESCE(p.Patent_Applications_Count, 0) <> 0 OR
        COALESCE(eh.Total_EU_Horizon_Funding, 0) <> 0 OR
        COALESCE(bf.Total_Business_Finland_Funding, 0) <> 0 OR
        COALESCE(bf.Total_Tutkimusrahoitus, 0) <> 0;
    """
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn)
    return df

