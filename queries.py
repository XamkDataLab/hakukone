import pyodbc
import streamlit as st
import pandas as pd

driver = st.secrets["driver"]
server = st.secrets["server"]
database = st.secrets["database"]
username = st.secrets["username"]
password = st.secrets["password"]

def get_company_names2():
    query = "SELECT DISTINCT yritys, y_tunnus FROM yritykset ORDER BY yritys;"
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn)
    return df

def fetch_horizon_data(y_tunnus):
    query = """SELECT * FROM EU_Horizon2 WHERE y_tunnus = ?;"""
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn, params=(y_tunnus,))
    return df
    
def fetch_eura_data(y_tunnus):
    query = """SELECT * FROM EURA2020 WHERE Y_tunnus = ?;"""
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn, params=(y_tunnus,))
    return df

def fetch_new_eura_data(y_tunnus):
    query = """SELECT * FROM EURA2027 WHERE Business_ID_of_the_implementing_organisation = ?;"""
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn, params=(y_tunnus,))
    return df
    
def fetch_legal_status_data():
    query = """
    SELECT 
        p.lens_id, 
        p.invention_title, 
        p.legal_status_anticipated_term_date,
        p.publication_type,
        a.extracted_name,
        a.applicant_basename,
        y.yritys,
        y.yhtiömuoto,
        y.y_tunnus
    FROM patents p
    LEFT JOIN applicants a ON p.lens_id = a.lens_id
    LEFT JOIN yritykset y ON a.applicant_basename = y.yritys_basename2
    WHERE p.legal_status_patent_status IS NOT NULL
    ORDER BY p.legal_status_anticipated_term_date ASC;
    """
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn)
    return df

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
    
def fetch_collaboration_data():
    query = """
    SELECT 
        c.FinnishOrgId, 
        c.FinnishOrgName, 
        c.CollaboratorOrgId, 
        c.CollaboratorOrgName, 
        c.CollaboratorCountry,
        c.ProjectId, 
        c.ProjectTitle,
        c.FinnishOrgContribution,
        c.ProjectRole,
        c.StartDate,
        c.EndDate,
        s.euroSciVocTitle
    FROM 
        horizon_collaborations c
    LEFT JOIN 
        horizon_europe_SciVoc s ON c.ProjectId = s.projectId;
    """
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn)
        
    return df

def fetch_data2(y_tunnus):
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
    
def fetch_individual_data(y_tunnus):
    query = """
    SELECT 
        y.y_tunnus,
        y.yritys,
        y.yritys_basename2,
        e.Toteutunut_EU_ja_valtion_rahoitus,
        m.applicationNumber AS DesignRights_ApplicationNumber,
        t.applicationNumber AS Trademarks_ApplicationNumber,
        p.lens_id AS Patent_Applications_Lens_Id,
        EU_Horizon.[Beneficiary’s contracted amount (EUR)],
        CAST(Business_Finland.Avustus as FLOAT) as Business_Finland_Funding
    FROM 
        yritykset y
    LEFT JOIN 
        eura2020 e ON y.y_tunnus = e.Y_tunnus AND y.y_tunnus = ?
    LEFT JOIN 
        mallioikeudet m ON y.yritys_basename = m.applicant_basename AND y.y_tunnus = ?
    LEFT JOIN 
        tavaramerkit t ON y.yritys_basename = t.applicant_basename AND y.y_tunnus = ?
    LEFT JOIN 
        applicants p ON y.yritys_basename2 = p.applicant_basename AND y.y_tunnus = ?
    LEFT JOIN 
        EU_Horizon ON y.yritys_basename2 = EU_Horizon.beneficiary_basename AND y.y_tunnus = ?
    LEFT JOIN 
        Business_Finland ON y.y_tunnus = Business_Finland.Y_tunnus AND y.y_tunnus = ?
    """
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn, params=(y_tunnus, y_tunnus, y_tunnus, y_tunnus, y_tunnus, y_tunnus))
        
    return df
    
def get_company_names():
    query = "SELECT DISTINCT yritys FROM yritykset ORDER BY yritys;"
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn)
    return df['yritys'].tolist()

def fetch_data3(yritys_name):
    # Define the SQL query
    query = """
    WITH Funding AS (
        SELECT 
            y.yritys,
            SUM(Toteutunut_EU_ja_valtion_rahoitus) as Total_Funding
        FROM 
            eura2020
        JOIN 
            yritykset y ON y.y_tunnus = eura2020.Y_tunnus
        WHERE 
            y.yritys = ?
        GROUP BY 
            y.yritys
    ),
    DesignRights AS (
        SELECT 
            y.yritys,
            COUNT(DISTINCT m.applicationNumber) as Design_Rights_Count
        FROM 
            mallioikeudet m
        JOIN 
            yritykset y ON y.yritys_basename = m.applicant_basename
        WHERE 
            y.yritys = ?
        GROUP BY 
            y.yritys
    ),
    Trademarks AS (
        SELECT 
            y.yritys,
            COUNT(DISTINCT t.applicationNumber) as Trademarks_Count
        FROM 
            tavaramerkit t
        JOIN 
            yritykset y ON y.yritys_basename = t.applicant_basename
        WHERE 
            y.yritys = ?
        GROUP BY 
            y.yritys
    ),
    Patents AS (
        SELECT 
            y.yritys,
            COUNT(DISTINCT p.lens_id) as Patent_Applications_Count
        FROM 
            applicants p
        JOIN 
            yritykset y ON y.yritys_basename2 = p.applicant_basename
        WHERE 
            y.yritys = ?
        GROUP BY 
            y.yritys
    ),
    EUHorizon AS (
        SELECT 
            y.yritys,
            SUM([Beneficiary’s contracted amount (EUR)]) as Total_EU_Horizon_Funding
        FROM 
            EU_Horizon
        JOIN yritykset y on y.yritys_basename2 = EU_Horizon.beneficiary_basename
        WHERE 
            y.yritys = ?
        GROUP BY 
            y.yritys
    ),
    BusinessFinland AS (
        SELECT 
            y.yritys,
            SUM(CAST(Avustus as FLOAT)) as Total_Business_Finland_Funding,
            SUM(CAST(Tutkimusrahoitus as FLOAT)) as Total_Tutkimusrahoitus
        FROM 
            Business_Finland
        JOIN yritykset y on y.y_tunnus = Business_Finland.Y_tunnus
        WHERE 
            y.yritys = ?
        GROUP BY 
            y.yritys
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
        COALESCE(bf.Total_Tutkimusrahoitus, 0) as Total_Tutkimusrahoitus
    FROM 
        yritykset y
    LEFT JOIN 
        Funding f ON y.yritys = f.yritys
    LEFT JOIN 
        DesignRights d ON y.yritys = d.yritys
    LEFT JOIN 
        Trademarks t ON y.yritys = t.yritys
    LEFT JOIN 
        Patents p ON y.yritys = p.yritys
    LEFT JOIN 
        EUHorizon eh ON y.yritys = eh.yritys
    LEFT JOIN 
        BusinessFinland bf ON y.yritys = bf.yritys
    WHERE 
        y.yritys = ?;
    """
    
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn, params=(yritys_name,)*7)  # Adjust the number of parameters as needed
        
    return df

def fetch_company_data(y_tunnus):
    query = """
    SELECT y.y_tunnus,
    y.yritys,
    p.date_published,
    p.publication_type,
    p.legal_status_patent_status,
    t.applicationDate
    FROM yritykset y
    LEFT JOIN applicants a ON y.yritys_basename = a.applicant_basename
    LEFT JOIN patents p ON a.lens_id = p.lens_id
    LEFT JOIN tavaramerkit t ON y.yritys_basename = t.applicant_basename
    WHERE y.y_tunnus = ?
    """
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        df = pd.read_sql(query, conn, params=(y_tunnus,))
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

def fetch_maakunta_cpc(maakunta):
    maakunta_cpc_query = """
    select y.y_tunnus,p.lens_id,p.invention_title,c.class, c.cpc_classification,d.title,pi.Postinumeroalue, pi.Maakunnan_nimi,pi.Kunnan_nimi, y.yritys,y.postinumero
    from yritykset y 
    left join applicants a on a.applicant_basename = y.yritys_basename2
    left join patents p on p.lens_id = a.lens_id
    left join cpc_classifications c on c.lens_id = p.lens_id
    left join cpc_descriptions d on d.cpc_code = c.cpc_code
    LEFT JOIN 
            Postinumeroalueet pi ON 
            CASE 
                WHEN RIGHT(y.postinumero, 1) = '1' THEN LEFT(y.postinumero, LEN(y.postinumero) - 1) + '0'
                ELSE y.postinumero
            END 
            = pi.Postinumeroalue
    where  is not null and pi.Maakunnan_nimi = ?
        """
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        maakunta_cpc_df = pd.read_sql_query(maakunta_cpc_query, conn, params=(y_tunnus,))
    return maakunta_cpc_df

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

def fetch_eura2027_collab():
    collab_query = """
            SELECT
        p1.Name_of_implementing_organisation AS Organization1,
        p2.Name_of_implementing_organisation AS Organization2,
        p1.Group_Project_code,
        p1.Rahasto,
        p1.Rahoittava_viranomainen,
        p1.Planned_public_funding,
        p1.Tukimuoto,
        p1.Tukitoimen_ala,
        p1.Sijainti
    FROM
        EURA2027 p1
    INNER JOIN
        EURA2027 p2 ON p1.Group_Project_code = p2.Group_Project_code AND p1.Name_of_implementing_organisation < p2.Name_of_implementing_organisation
    WHERE
        p1.Group_Project_code IS NOT NULL
    GROUP BY
        p1.Group_Project_code, p1.Name_of_implementing_organisation, p2.Name_of_implementing_organisation, p1.Rahasto, p1.Rahoittava_viranomainen,
        p1.Planned_public_funding, p1.Tukimuoto,p1.Tukitoimen_ala,p1.Sijainti
        """
    with pyodbc.connect(f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}') as conn:
        collab_df = pd.read_sql_query(collab_query, conn)
    return collab_df
    
