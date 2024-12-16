import polars as pl
import streamlit as st

# funzione che carica i dataset
def load_data():
    
    values = pl.read_csv(
    
        source = "values.csv"
        
        # rimuovo le osservazioni superflue
        ).filter(
        pl.col("recordID") != 228540
        
        # rimuovo le colonne superflue
        ).select(
            pl.col("*").exclude("recordID")
        
        )
    
    lakeinformation = pl.read_csv(
    
        source = "lakeinformation.csv",
        encoding = "utf8-lossy"
        
        # rimuovo le colonne superflue
        ).select(
            pl.col("*").exclude("contributor", "Other_names", "geospatial_accuracy_km", "sampling_time_of_day", "time_period")
        
        # rimuovo le osservazioni superflue
        ).filter(
            pl.col("siteID") < 342
        
        # aggiusto i nomi dei laghi
        ).with_columns(
            pl.col("Lake_name").str.replace_all(r"\.", " ")
        
        # formatto la colonna "lake_or_reservoir"
        ).with_columns(
            pl.col("lake_or_reservoir").str.replace("l", "L").str.strip_chars_end(" ")
        )

    return values, lakeinformation


# caricamento dei dataset
data, lakeinformation = load_data()

# visualizzazione dei dataset
st.write(data, lakeinformation)