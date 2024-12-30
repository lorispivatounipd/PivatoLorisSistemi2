import polars as pl
import streamlit as st
import plotly.graph_objects as go
import altair as alt
from vega_datasets import data as countries_data

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

# Funzione che prende una riga di un dataframe e ritorna un dataframe
# con valori 0.5 al posto dei valori mancanti
def convert_null(df):
    
    # Riorganizzazione del dataframe
    df = df.pivot(on = "year", values = "value")
    
    # Colonne che devono rimanere invariate
    columns_to_keep = df.columns[:2]
    
    # Trasformazione in valori nulli dei valori in eccesso
    df1 =  df.select([
        pl.col(c) if c in columns_to_keep else pl.lit(None).alias(c)
        for c in df.columns
    ])
    
    # Controllo per colonne non presenti a causa dei valori mancanti
    columns_to_add = [str(year) for year in range(1985, 2010)]
    
    # Controlla se la colonna esiste e d eventualmente la aggiunge
    for col in columns_to_add:
        if col not in df1.columns:
            df1 = df1.with_columns(pl.lit(0.5).alias(col))
    
    # Riorganizzazione del dataframe
    df1 = df1.unpivot(
            on = [str(year) for year in range(1985, 2010)]
        
        # Eliminazione dei valori nulli
        ).drop_nulls(
        ).with_columns(
            pl.lit("No data").alias("label")
        ).rename(
            {"variable": "year"}
        ).with_columns(
            pl.col("year").cast(pl.Int64).alias("year"))
    
    return df1

# Funzione che ritorna l'ID del lago selezionato
def get_lake(lakeinformation):
    
    # Costruzione di colonne per una migliore visualizzazione del selectbox
    col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
    
    # Scelta del lago
    lake = col2.selectbox("Inserisci il lago:", lakeinformation.get_column("Lake_name").sort())

    # Determinazione dell'ID del lago
    return lakeinformation.filter(pl.col("Lake_name") == lake)["siteID"]

# Funzione che costruisce lo scattermapbox
def get_map_interactive(lakeID):
    
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

    # Visualizzazione della mappa
    st.plotly_chart(fig, use_container_width = True)

# Funzione che costruisce i boxplot
def get_boxplot(data, lakeinformation):
    
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
        alt.Color("region", title = "Regione").scale(scheme="category10"),
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

# Funzione che costruisce l'heatmap
def get_rect(data, lakeinformation):
    
    # Costruzione di colonne per una migliore visualizzazione del selectbox
    col1, col2 = st.columns([0.3, 0.7])
    
    # Costruzione del selectbox delle regioni
    region = col1.selectbox("Regione:", lakeinformation.get_column("region").unique().sort())
    
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
    
    # Visualizzazione dell'heatmap
    st.altair_chart(graph)

# Funzione che costruisce il grafico della temperatura dell'aria nel tempo in inverno, annuale ed in estate
def get_lineplot_air_temp(data, lakeID):
    
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

    # Visualizzazione del grafico
    st.altair_chart(chart, use_container_width = True)

# Funzione che costruisce i tre barplot della copertura nuvolosa in inverno, annuale ed in estate
def get_barplot_cloud(data, lakeID):
    
    # Suddivisione del dataframe per semplificarne l'utilizzo
    data_winter = data.filter(
        pl.col("variable") == "Cloud_Cover_Winter",
        pl.col("siteID") == lakeID)
    data_annual = data.filter(
        pl.col("variable") == "Cloud_Cover_Annual",
        pl.col("siteID") == lakeID)
    data_summer = data.filter(
        pl.col("variable") == "Cloud_Cover_Summer",
        pl.col("siteID") == lakeID)
    
    # Creo un select point per marcare una barra quando selezionata
    select = alt.selection_point(name = "select", on = "click")
    
    # Creo un select point per evidenziare una barra al passaggio del cursore
    highlight = alt.selection_point(name = "highlight", on = "pointerover", empty = False)

    # Creo una funzione che definisce lo spessore della barra all'interazione
    stroke_width = (
        
        # Spessore 4 quando la barra viene selezionata
        alt.when(select).then(alt.value(4, empty=False))
        
        # Spessore 2 quando avviene il passaggio del cursore
        .when(highlight).then(alt.value(2))
        
        # Spessore 0 altrimenti
        .otherwise(alt.value(0))
    )

    # Barplot della copertura nuvolosa in inverno
    cloud1 = alt.Chart(data_winter,
        
        # Altezza del grafico
        height=200
    
    # Definizione delle barre
    ).mark_bar(
        
        fill = "#4C78A8", # Colore della barra
        stroke = "black", # Colore del bordo
        cursor = "pointer", # Tipologia dell'interazione col cursore
        size = 25 # Larghezza della barra
        
    ).encode(
        
        # Asse X
        alt.X("year", axis = alt.Axis(format = ".0f"), scale = alt.Scale(zero = False), title = ""),
        
        # Asse Y
        alt.Y("value:Q", scale = alt.Scale(domain = [0, 1]), title="Inverno"),
        
        # Definizione delle informazioni mostrate sopra il cursore al suo passaggio
        tooltip = [alt.Tooltip("value", title = "Percentuale"), alt.Tooltip("year", title="Anno")],
        
        # Definizione dell'opacità delle barre quando una viene selezionata
        fillOpacity = alt.when(select).then(alt.value(1)).otherwise(alt.value(0.3)),
        
        # Larghezza del bordo delle barre
        strokeWidth = stroke_width,
        
    # Aggiunta dei parametri per l'interazione
    ).add_params(select, highlight)

    # Barplot della copertura nuvolosa media annuale
    cloud2 = alt.Chart(data_annual,
            height = 200
    ).mark_bar(
        fill = "#4C78A8",
        stroke = "black",
        cursor = "pointer",
        size = 25
    ).encode(
        alt.X("year", axis = alt.Axis(format = ".0f"), scale = alt.Scale(zero = False), title = ""),
        alt.Y("value:Q", scale = alt.Scale(domain = [0, 1]), title = "Annuale"),
        tooltip = [alt.Tooltip("value", title = "Percentuale"), alt.Tooltip("year", title = "Anno")],
        fillOpacity = alt.when(select).then(alt.value(1)).otherwise(alt.value(0.3)),
        strokeWidth = stroke_width,
    ).add_params(select, highlight)

    # Barplot della copertura nuvolosa in inverno
    cloud3 = alt.Chart(data_summer,
            height=200
    ).mark_bar(
        fill="#4C78A8",
        stroke="black",
        cursor="pointer",
        size=25
    ).encode(
        alt.X("year", axis = alt.Axis(format = ".0f"), scale = alt.Scale(zero = False), title = ""),
        alt.Y("value:Q", scale = alt.Scale(domain = [0, 1]), title = "Estate"),
        tooltip = [alt.Tooltip("value", title = "Percentuale"), alt.Tooltip("year", title = "Anno")],
        fillOpacity = alt.when(select).then(alt.value(1)).otherwise(alt.value(0.3)),
        strokeWidth = stroke_width,
    ).add_params(select, highlight)

    # Inserimento del testo "No data" nei valori mancanti del barplot invernale
    text1 = alt.Chart(
        convert_null(data_winter)
        
    # Definizione del testo
    ).mark_text(
        align = "left",
        baseline = "bottom",
        fontSize = 14,
        fontWeight = 600,
        color = "black",
        angle = 90 # Rotazione del testo per renderlo verticale
    ).encode(
        x = "year",
        y = "value",
        text = "label"
    )
    
    # Inserimento del testo "No data" nei valori mancanti del barplot annuale
    text2 = alt.Chart(
        convert_null(data_annual)
        
    ).mark_text(
        align = "left",
        baseline = "bottom",
        fontSize = 14,
        fontWeight = 600,
        color = "black",
        angle = 90
    ).encode(
        x = "year",
        y = "value",
        text = "label"
    )

    # Inserimento del testo "No data" nei valori mancanti del barplot estivo
    text3 = alt.Chart(
        convert_null(data_summer)
        
    ).mark_text(
        align = "left",
        baseline = "bottom",
        fontSize = 14,
        fontWeight = 600,
        color = "black",
        angle = 90
    ).encode(
        x = "year",
        y = "value",
        text = "label"
    )

    # Visualizzazione dei tre barplot
    if convert_null(data_winter).is_empty(): st.altair_chart(cloud1 , use_container_width = True)
    else: st.altair_chart(cloud1 + text1 , use_container_width = True)
    
    if convert_null(data_annual).is_empty(): st.altair_chart(cloud2, use_container_width = True)
    else: st.altair_chart(cloud2 + text2, use_container_width = True)
    
    if convert_null(data_summer).is_empty(): st.altair_chart(cloud3, use_container_width = True)
    else: st.altair_chart(cloud3 + text3, use_container_width = True)

# Funzione che costruisce il grafico della radiazione totale in inverno, annuale ed in estate
def get_lineplot_radiation(data, lakeID):
    
    # Filtro del dataframe per semplificarne l'utilizzo
    data_rad = data.filter(
            pl.col("variable").is_in(["Radiation_Total_Summer", "Radiation_Total_Annual", "Radiation_Total_Winter"]),
            pl.col("siteID") == lakeID
        )
    
    # Creazione di un dominio per una migliore visualizzazione del grafico
    custom_domain = [
        data_rad.min()["value"][0] - 50,
        data_rad.max()["value"][0] + 50
    ]
    
    # Creazione del grafico
    chart = alt.Chart(
        data_rad
        
    # Implementazione del gradiente colorato
    ).mark_area(
        opacity = 0.3,
        line = {"color": "black"},
        color = alt.Gradient(
            gradient = "linear",
            stops = [
                alt.GradientStop(color = "white", offset = 0),
                alt.GradientStop(color = "", offset = 1)
            ],
            x1 = 1,
            x2 = 10,
            y1 = 1,
            y2 = 1
        )
        
    ).encode(
        # Asse X
        alt.X("year:Q", axis = alt.Axis(format = ".0f"), title = "Anno"),
        # Asse Y
        alt.Y("value:Q", title = "Radiazioni", scale = alt.Scale(domain = custom_domain)).stack(None),
        # Colori delle linee
        alt.Color("variable"),
        # Rimozione del tootip
        tooltip = alt.value(None)
        
    ).properties(
        height = 300
    )

    # Visualizzazione del grafico
    st.altair_chart(chart, use_container_width = True)

# Funzione che costruisce la mappa per visualizzare il metodo di campionamento
def get_map_method(countries_data, lakeinformation):
    
    # Ricavo le informazioni per costruire la mappa del mondo
    countries = alt.topo_feature(countries_data.world_110m.url, "countries")

    # Costruzione della mappa del mondo
    background = alt.Chart(countries).mark_geoshape(
        fill = "lightgray",
        stroke = "white",
        tooltip = None
    ).project("equirectangular").properties(
        # width=500,
        # height=400
    )

    # Inserimento dei laghi sulla mappa
    figure = alt.Chart(lakeinformation).mark_circle().encode(
        longitude = "longitude:Q",
        latitude = "latitude:Q",
        size = alt.value(15),
        # Distinzione del metodo per colori
        color = alt.Color("source").scale(range=["blue", "red"]),
        # Modifica del tooltip
        tooltip = [alt.Tooltip("Lake_name", title = "Nome"),
                   alt.Tooltip("location", title="Stato"),
                   alt.Tooltip("source", title="Metodo")]
    ).project(
        "equirectangular"
    ).properties(
        # width=500,
        # height=400
    )

    # Visualizzazione del grafico finale
    st.altair_chart(background + figure, use_container_width=True)

# Funzione che ritorna il titolo e l'introduzione
def start_page():
    
    # Inserimento del titolo centrato
    style_heading = "text-align: center"
    st.markdown(f"<h1 style='{style_heading}'>Studio dell'effetto del riscaldamento globale sulle temperature superficiali dell'acqua dei laghi</h1>", unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([0.15, 0.7, 0.15])

    # Inserimento dell'introduzione
    col2.markdown("""Il cambiamento ambientale globale ha influenzato le temperature superficiali dei laghi, un fattore chiave per la struttura e
    la funzione degli ecosistemi.  
    Studi recenti hanno suggerito un riscaldamento significativo delle temperature dell'acqua in laghi individuali
    in molte regioni del mondo.  
    Tuttavia, la coerenza spaziale e temporale associata all'entità di queste tendenze rimane poco chiara.  
    Pertanto, è necessario un set di dati globale sulle temperature dell'acqua per comprendere e sintetizzare le tendenze a lungo termine
    delle temperature superficiali delle acque interne.  
    E' stato assemblato un [database](https://search.dataone.org/view/https%3A%2F%2Fpasta.lternet.edu%2Fpackage%2Fmetadata%2Feml%2Fknb-lter-ntl%2F10001%2F4) delle temperature superficiali estive di 291 laghi,
    raccolte in situ e/o tramite satelliti, perun periodo di 25 anni (1985-2009). Inoltre, per ciascun lago sono stati raccolti i relativi fattori
    climatici (*temperature dell'aria, radiazione solare e copertura nuvolosa*) e le caratteristiche geomorfometriche (*latitudine, longitudine,
    altitudine, superficie del lago, profondità massima, profondità media e volume*) che influenzano le temperature superficiali dei laghi.""")
    
    col2.divider()


# Funzione che ritorna il contesto e la sintesi
def background():

    col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
    
    col2.markdown("""
    ## Conteso e Sintesi
    Gli ecosistemi di acqua dolce sono vulnerabili agli effetti dei cambiamenti ambientali globali.
    I laghi sono sentinelle del cambiamento climatico e rappresentano un efficace indicatore della risposta limnologica
    al cambiamento climatico globale, poiché integrano fattori climatici e paesaggistici. Le temperature superficiali dei
    laghi possono influenzare, direttamente o indirettamente, i processi fisici, chimici e biologici di un lago,
    inclusa la temperatura della zona fotosintetica, la stabilità della colonna d'acqua, la produttività primaria
    del lago, i cambiamenti di distribuzione delle specie ittiche e le interazioni tra specie.  
    I fattori climatici, tra cui la temperatura dell'aria, la copertura nuvolosa e la radiazione solare,
    insieme ai fattori geomorfometrici, come l'area superficiale e la profondità del lago, influenzano le temperature
    superficiali dell'acqua nei laghi.  
    Tra il 1986 e il 2005, le temperature globali dell'aria sono aumentate di 0,61 °C ([riferimento](https://scholar.google.com/scholar_lookup?title=IPCC%20fifth%20assessment%20report%2C%20climate%20change%202013%3A%20The%20physical%20science%20basis&journal=IPCC&volume=AR5&pages=31-39&publication_year=2013&author=Hartmann%2CDL&author=Tank%2CAMGK&author=Rusticucci%2CM)).
    Le temperature dell'acqua sono aumentate nelle ultime decadi, in concomitanza con il cambiamento delle temperature dell'aria,
    con poche eccezioni. Generalmente, le temperature dell'acqua tendono a riflettere quelle regionali dell'aria,
    riscaldandosi o raffreddandosi a tassi simili. Tuttavia, in alcune regioni, come quella dei Grandi Laghi
    del Nord America e dell'Europa settentrionale, i corpi idrici si riscaldano più rapidamente rispetto all'aria
    circostante.  
    La radiazione solare è una componente chiave del bilancio termico dei laghi. L'aumento della radiazione solare
    incidente incrementa le temperature medie dei laghi. La copertura nuvolosa può ridurre la radiazione solare incidente,
    ma al contempo comporta una maggiore radiazione a onde lunghe. Di conseguenza, l'influenza
    della copertura nuvolosa sulle temperature dei laghi può essere bidirezionale e complessa.
    Le proprietà specifiche di un lago, come profondità, superficie e volume, possono modulare gli effetti di questi
    fattori climatici e influenzare le temperature dei laghi. Ad esempio, le temperature superficiali dell'acqua
    risultano inversamente correlate con la profondità media. In generale, i laghi più bassi tendono a riscaldarsi
    più rapidamente e a presentare temperature superficiali più elevate rispetto ai laghi profondi, che hanno maggiori capacità
    di immagazzinare calore. Tuttavia, su ampia scala spaziale, i fattori climatici esercitano un'influenza maggiore sulle
    temperature superficiali rispetto alla morfologia del lago.""")
    
    # Creazione di un container per una migliore visualizzazione
    cont = st.container(border = True)
    
    # Creazione del caption
    cont.caption("Boxplot delle temperature dei laghi")
    
    # Visualizzazione dei boxplot
    cont.altair_chart(get_boxplot(data, lakeinformation), use_container_width = True)
    
    st.divider()


# Caricamento dei dataset
data, lakeinformation = load_data()

# Inserimento del titolo e dell'introduzione
start_page()

# Inserimento del contesto e sintesi
background()

# Scelta del lago
lakeID = get_lake(lakeinformation)

# Visualizzazione del grafico delle temperature dell'aria
get_lineplot_air_temp(data, lakeID)

# Visualizzazione dello scattermapbox
get_map_interactive(lakeID)

# Visualizzazione della mappa per vedere i metodi di campionamento
get_map_method(countries_data, lakeinformation)

# Visualizzazione dell'heatmap con selezione per regione
get_rect(data, lakeinformation)

# Visualizzazione dei barplot della copertura nuvolosa in inverno, annuale ed in estate
get_barplot_cloud(data, lakeID)

# Visualizzazione del grafico della radiazione totale in inverno, annuale ed in estate
get_lineplot_radiation(data, lakeID)
