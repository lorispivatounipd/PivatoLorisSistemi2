import polars as pl
import streamlit as st
import plotly.graph_objects as go
import altair as alt

# Configurazione della pagina web
st.set_page_config(
    layout = "wide",
    initial_sidebar_state = "collapsed",
    page_title = "Lake temperatures"
)

# Funzione che carica i dataset
def load_data():
    
    # Dataset con i valori
    values = pl.read_csv(
    
        source = "values.csv"
        
        # Rimuovo le osservazioni superflue
        ).filter(
        pl.col("recordID") != 228540
        
        # Rimuovo le colonne superflue
        ).select(
            pl.col("*").exclude("recordID")
        
        )
    
    # Dataset con le informazioni per lago
    lakeinformation = pl.read_csv(
    
        source = "lakeinformation.csv",
        encoding = "utf8-lossy"
        
        # Rimuovo le colonne superflue
        ).select(
            pl.col("*").exclude("contributor", "Other_names", "geospatial_accuracy_km", "sampling_time_of_day", "time_period")
        
        # Rimuovo le osservazioni superflue
        ).filter(
            pl.col("siteID") < 342
        
        # Aggiusto i nomi dei laghi
        ).with_columns(
            pl.col("Lake_name").str.replace_all(r"\.", " ")
        
        # Formatto la colonna "lake_or_reservoir"
        ).with_columns(
            pl.col("lake_or_reservoir").str.replace("l", "L").str.strip_chars_end(" ")
        
        # Traduco in italiano la colonna "region"
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

# Funzione che costruisce i boxplot
def get_boxplot(_data, _lakeinformation):
    
    # Riordino e pulizia dei dati per semplicità d'utilizzo
    graph_data = data.filter(
        
            (pl.col("variable").is_in(["Lake_Temp_Summer_InSitu", "Lake_Temp_Summer_Satellite"]))
        
        ).pivot(
        
            on = "variable",
            values = "value"
        
        ).join(
        
            lakeinformation,
            on = "siteID"
        
        ).with_columns(
        
            pl.when(pl.col("source") == "in situ").then(pl.col("Lake_Temp_Summer_InSitu"))
            .when(pl.col("source") == "satellite").then(pl.col("Lake_Temp_Summer_Satellite"))
            .otherwise(None)
            .alias("Lake_Temp_Summer")
        
        ).select(
            pl.col("Lake_Temp_Summer", "region", "year", "Lake_name")
        )
    
    # Costruzione dello scatterplot
    scatter = alt.Chart(graph_data).mark_circle(
        
        binSpacing = 0,
        size = 8,
        opacity = 1
        
    ).encode(
        
        alt.Y("Lake_Temp_Summer", title = "Temperatura (°C)"),
        alt.X("year:O", title = "Anno"),
        alt.Color("region").scale(scheme="category10"),
        # Offset dei singoli punti in modo randomico
        xOffset = "jitter:Q",
        # Visualizzazione del nome del lago al passaggio del cursore
        tooltip = "Lake_name"
        
    # Formula che genera un offset secondo la trasformazione di Box-Muller
    ).transform_calculate(
        jitter = "sqrt(-2*log(random()))*cos(2*PI*random())"
    ).properties(
        height = 500
    )

    # Costruzione del boxplot
    boxplot = alt.Chart(graph_data).mark_boxplot(
        
        # Rimuovo i valori outliers già visibili con lo scatterplot
        outliers = False,
        size = 25,
        # Rendo l'area delle scatole invisibile per visualizzare gli scatter sottostanti
        box = {"fill": None}
        
    ).encode(
        
        alt.Y("Lake_Temp_Summer", title = ""),
        alt.X("year:O"),
        # Rendo i bordi dei boxplot visibili
        stroke = alt.value("black"),
        strokeWidth = alt.value(1.5)
        
    )

    # Grafico finale
    final_chart = scatter + boxplot
    
    return final_chart

# Funzione che ricava l'heatmap
def get_rect(data, lakeinformation):
    
    # Costruzione del selectbox delle regioni
    region = st.selectbox("Regione:", lakeinformation.get_column("region").unique().sort())
    
    # Unione dei due dataframe
    data_temp = data.join(
        
        lakeinformation,
        on = "siteID"
        
    ).filter(
        
        pl.col("variable").is_in(["Lake_Temp_Summer_Satellite", "Lake_Temp_Summer_InSitu"]),
        pl.col("region") == region
    
    )

    # Costruzione dell'heatmap
    graph = alt.Chart(data_temp).mark_rect().encode(
        
        alt.X("Lake_name:O", title = "Lago"),
        alt.Y("year:O", sort = "descending", title = "Anno"),
        alt.Color("value:Q", title = "Temperatura", scale = alt.Scale(
            
            scheme = "blueorange",
            # reverse = True,
            # domain = [0, 30] # Il dominio è [0,30] per permettere il confronto dei vari heatmap
            
        ))
        
    ).properties(
        
        height = 500,
        # larghezza che permette di visualizzare bene tutti gli heatmap
        width = data_temp.select("siteID").unique().height * 13.8158 + 156
    )
    
    return graph

# Funzione che ricava il grafico della temperatura dell'aria nel tempo
def get_lineplot(data, lakeID):
    
    # Crea un selection point che identifica il punto più vicino al cursore basato sull'asse X "Anno"
    nearest = alt.selection_point(
        
        nearest = True,
        on = "pointerover",
        fields = ["year"],
        empty = False
    )

    # Il grafico di base con le temperature
    line = alt.Chart(
        
        data.filter(
            pl.col("variable").is_in(["Air_Temp_Mean_Annual_CRU", "Air_Temp_Mean_Summer_CRU", "Air_Temp_Mean_Winter_CRU"]),
            pl.col("siteID") == lakeID
        )
        
    ).mark_line().encode(
        # Asse X
        alt.X("year:Q", axis = alt.Axis(format = ".0f"), scale = alt.Scale(zero = False), title = "Anno"),
        # Asse Y
        alt.Y("value:Q", scale = alt.Scale(zero = False), title = "Temperatura (°C)"),
        # Colori delle linee
        alt.Color("variable")
    )

    # Selettore trasparente del grafico. Ricava il valore X in cui si trova il cursore
    selectors = alt.Chart(
        
        data.filter(
            pl.col("variable").is_in(["Air_Temp_Mean_Annual_CRU", "Air_Temp_Mean_Summer_CRU", "Air_Temp_Mean_Winter_CRU"]),
            pl.col("siteID") == lakeID
        )
        
    ).mark_point().encode(
        
        alt.X("year:Q", title = "Anno"),
        opacity = alt.value(0)
        
    ).add_params(
        nearest
    )
    
    # Disegna i punti sulle linee per evidenziare l'anno selezionato
    points = line.mark_point().encode(
        opacity = alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Riporta la temperatura delle linee nei punti selezionati con il cursore
    text = line.mark_text(
        align = "left",
        dx = 5,
        dy = -5
    ).encode(
        text = alt.condition(nearest, "value", alt.value(" "))
    )

    # Disegna la linea verticale in corrispondenza dell'anno selezionato con il cursore
    rules = alt.Chart(
        
        data.filter(
            pl.col("variable").is_in(["Air_Temp_Mean_Annual_CRU", "Air_Temp_Mean_Summer_CRU", "Air_Temp_Mean_Winter_CRU"]),
            pl.col("siteID") == lakeID
        )
        
    ).mark_rule(color = "gray").encode(
        alt.X("year:Q", title = "Anno"),
        opacity = alt.value(0.3)
    ).transform_filter(
        nearest
    )
    
    # Grafico finale che combina i grafici precedenti
    chart = alt.layer(
      line, selectors, points, rules, text
    ).properties(
        height=300
    )

    return chart


# Caricamento dei dataset
data, lakeinformation = load_data()

# Scelta del lago
lake = st.selectbox("Inserisci il lago:", lakeinformation.get_column("Lake_name").sort())

# Determinazione dell'ID del lago
lakeID = lakeinformation.filter(pl.col("Lake_name") == lake)["siteID"]

# Visualizzazione del grafico delle temperature dell'aria
st.altair_chart(get_lineplot(data, lakeID), use_container_width = True)

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

# Visualizzazione dei boxplot
st.altair_chart(get_boxplot(data, lakeinformation), use_container_width = True)

# Visualizzazione dell'heatmap con selezione per regione
st.altair_chart(get_rect(data, lakeinformation))
