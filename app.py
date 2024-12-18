import polars as pl
import streamlit as st
import plotly.graph_objects as go

# configurazione della pagina web
st.set_page_config(
    layout = "wide",
    initial_sidebar_state = "collapsed"
)

# Funzione che carica i dataset
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
        
        # traduco in italiano la colonna "region"
        ).with_columns(
            pl.col("region").replace([
                "Europe", "Middle East", "Northeastern North America", "South America", "Southeastern North America", "Western North America"
            ], [
                "Europa", "Medio Oriente", "Nord America nord-orientale", "Sud America", "Nord America sud-orientale", "Nord America occidentale"
            ])
        )

    return values, lakeinformation

# Funzione che costruisce lo scattermapbox
def get_map():
    
    # Color map personalizzato
    color_map = {
        "Africa": "#1f77b4",
        "Asia": "#ff7f0e",
        "Europa": "#2ca02c",
        "Medio Oriente": "#d62728",
        "Nord America nord-orientale": "#9467bd",
        "Nord America occidentale": "#8c564b",
        "Nord America sud-orientale": "#e377c2",
        "Oceania": "#7f7f7f",
        "Sud America": "#bcbd22"
    }
    
    # Creazione della figura
    fig = go.Figure()
    
    # Aggiungo una traccia per ciascuna regione
    
    for region, color in color_map.items():
        
        # Filtro i dati per la regione corrente
        region_data = lakeinformation.filter(pl.col("region") == region)
        
        # Aggiungo una traccia
        fig.add_trace(
            
            go.Scattermapbox(
                
                lat = region_data["latitude"],
                lon = region_data["longitude"],
                mode = "markers",
                name = region, # Nome della regione mostrato nella legenda
                marker = dict(
                    
                    size = 8,
                    color = color  # Colore specifico per la regione
                    
                ),
                text = region_data["Lake_name"], # Testo di hover
                hoverinfo = "text",
                hoverlabel = dict( # Configurazione dell'hover
                    
                    bordercolor = "black", # Colore del bordo
                    bgcolor = "white", # Colore del background
                    font = dict(
                        
                        color = "black",
                        size = 18,
                        family = "Arial"
                        
                    )
                )
            )
        )
    
    # Configurazione della mappa
    fig.update_layout(
        
        mapbox = dict(
            
            style = "carto-positron",
            zoom = 1
            
        ),
        margin = dict(l=0, r=0, t=0, b=0), # Configurazione dei margini
        showlegend = True # Mostra la legenda
        
    )
    
    return fig

# Caricamento dei dataset
data, lakeinformation = load_data()

# Visualizzazione dei dataset
st.write(data, lakeinformation)

# Scelta del lago
lake = st.selectbox("Inserisci il lago:", lakeinformation.get_column("Lake_name").sort())

# Determinazione dell'ID del lago
lakeID = lakeinformation.filter(pl.col("Lake_name") == lake)["siteID"]

# Ricavo lo scattermapbox base
fig = get_map()

# Ricavo le informazioni del lago selezionato
lake_selected = lakeinformation.filter(pl.col("siteID") == lakeID)

# Colora il dot del lago selezionato di rosso ed evidenzia il nome del lago
fig.add_trace(go.Scattermapbox(
    
    lat = lake_selected["latitude"],
    lon = lake_selected["longitude"],
    mode = "text+markers",
    # caratteristiche del marker
    marker = dict(
        
        color = "#ff0000",
        size = 12,
        symbol = "circle"
    ),
    showlegend = False,
    hovertext = lake_selected["Lake_name"],
    text = lake_selected["Lake_name"],
    hoverinfo = "text",
    # caratteristiche dell'hover text
    hoverlabel = dict(
        
        bordercolor = "black",
        bgcolor = "white",
        # caratteristiche del testo nell'hover text
        font = dict(
            
            color = "black",
            size = 18,
            family = "Arial"
        )
    ),
    # caratteristiche del nome visualizzato sopra il marker
    textfont = dict(
        
        color = "black",
        size = 16
    ),
    textposition = "top center"
))


# Configurazione della mappa
# (Questa parte di codice non è stata inserita nella fnuzione get_map perchè la mappa
# si aggiorna ad ogni ricentratura dovuta dalla selezione di un lago)
fig.update_layout(
    mapbox = dict(
        
        style = "carto-positron",
        zoom = 1,
        # centratura della mappa in base al lago selezionato
        center = dict(
            
            lat = lake_selected["latitude"][0],
            lon = lake_selected["longitude"][0]
        )
    ),
    height = 300
)

# Visualizzazione dello scattermapbox
st.plotly_chart(fig, use_container_width=True)