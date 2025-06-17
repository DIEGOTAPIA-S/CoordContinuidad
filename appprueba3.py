import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, Search, LocateControl, Fullscreen, MarkerCluster
from shapely.geometry import Point, Polygon, shape, mapping # <<< CAMBIO: mapping añadido >>>
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import base64
from io import BytesIO
import tempfile
import unicodedata

# --- Imports para Vizzu ---
from streamlit_vizzu import VizzuChart
from ipyvizzu import Data, Config, Style

# Configuración de la página
st.set_page_config(page_title="Continuidad del Negocio", 
                page_icon="assets/logo_colmedica.png",layout="wide",  initial_sidebar_state="expanded"
)
st.title("🚨 Sistema de Gestión de Continuidad del Negocio")


# Límites para optimización
MAX_MARKERS = 3000  # Máximo de marcadores en el mapa

# ---------- CONFIGURACIÓN DE MAPAS ----------
TILES = {
    "MapLibre": {
        "url": "https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=dhEAG0dMVs2vmsaHdReR",
        "attr": '<a href="https://www.maptiler.com/copyright/" target="_blank">© MapTiler</a>'
    },
    "OpenStreetMap": {
        "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": 'OpenStreetMap'
    }
}

# ---------- SEDES FIJAS ----------
SEDES_FIJAS = {
    # ... (Tu diccionario de sedes fijas permanece sin cambios) ...
    "Colmédica Belaire": {"direccion": "Centro Comercial Belaire Plaza, Cl. 153 #6-65, Bogotá", "coordenadas": [4.729454000113993, -74.02444216931787], "color": "blue", "icono": "hospital"},
    "Colmédica Bulevar Niza": {"direccion": "Centro Comercial Bulevar Niza, Av. Calle 58 #127-59, Bogotá", "coordenadas": [4.712693239837536, -74.07140074602322], "color": "blue", "icono": "hospital"},
    "Colmédica Calle 185": {"direccion": "Centro Comercial Santafé, Cl. 185 #45-03, Bogotá", "coordenadas": [4.763543959141223, -74.04612616931786], "color": "blue", "icono": "hospital"},
    "Colmédica Cedritos": {"direccion": "Edificio HHC, Cl. 140 #11-45, Bogotá", "coordenadas": [4.718879348342116, -74.03609218650581], "color": "blue", "icono": "hospital"},
    "Colmédica Chapinero": {"direccion": "Cr. 7 #52-53, Chapinero, Bogotá", "coordenadas": [4.640908410923512, -74.06373898409286], "color": "blue", "icono": "hospital"},
    "Colmédica Colina Campestre": {"direccion": "Centro Comercial Sendero de la Colina, Cl. 151 #54-15, Bogotá", "coordenadas": [4.73397996072128, -74.05613864417634], "color": "blue", "icono": "hospital"},
    "Colmédica Centro Médico Colmédica Country Park": {"direccion": "Autopista Norte No 122 - 96, Bogotá", "coordenadas": [4.670067290638234, -74.05758327116473], "color": "blue", "icono": "hospital"},
    "Colmédica Metrópolis": {"direccion": "Centro Comercial Metrópolis, Av. Cra. 68 #75A-50, Bogotá", "coordenadas": [4.6812256618088615, -74.08315698409288], "color": "blue", "icono": "hospital"},
    "Colmédica Multiplaza": {"direccion": "Centro Comercial Multiplaza, Cl. 19A #72-57, Bogotá", "coordenadas": [4.652573284106405, -74.12629091534289], "color": "blue", "icono": "hospital"},
    "Colmédica Plaza Central": {"direccion": "Centro Comercial Plaza Central, Cra. 65 #11-50, Bogotá", "coordenadas": [4.633464230539147, -74.11621916981814], "color": "blue", "icono": "hospital"},
    "Colmédica Salitre Capital": {"direccion": "Capital Center II, Av. Cl. 26 #69C-03, Bogotá", "coordenadas": [4.660602588141229, -74.10864383068576], "color": "blue", "icono": "hospital"},
    "Colmédica Suba": {"direccion": "Alpaso Plaza, Av. Cl. 145 #103B-69, Bogotá", "coordenadas": [4.7499608085787575, -74.08737693178564], "color": "blue", "icono": "hospital"},
    "Colmédica Centro Médico Torre Santa Bárbara": {"direccion": "Autopista Norte No 122 - 96, Bogotá", "coordenadas": [4.70404406297091, -74.053790252428], "color": "blue", "icono": "hospital"},
    "Colmédica Unicentro Occidente": {"direccion": "Centro Comercial Unicentro Occidente, Cra. 111C #86-05, Bogotá", "coordenadas": [4.724354935414492, -74.11430016931786], "color": "blue", "icono": "hospital"},
    "Colmédica Usaquén": {"direccion": "Centro Comercial Usaquén, Cra. 7 #120-20, Bogotá", "coordenadas": [4.6985109910547695, -74.03076183068214], "color": "blue", "icono": "hospital"},
     "Centro Médico Colmédica Barranquilla Alto Prado": {"direccion": "Centro Comercial Cenco Altos del Prado, Calle 76 # 55-52, Barranquilla", "coordenadas": [11.004448920487901, -74.80367483068213], "color": "blue", "icono": "hospital"},
     "Centro Médico Colmédica Bucaramanga": {"direccion": "Cl 52 A 31 - 68 , Bucaramanga", "coordenadas": [7.115442288584315, -73.11191898409285], "color": "blue", "icono": "hospital"},
     "Centro Médico Colmédica Cali": {"direccion": "Cr 40 5C – 118 , Cali", "coordenadas": [3.4222730018219965, -76.543009], "color": "blue", "icono": "hospital"},
     "Centro Médico Colmédica Las Ramblas": {"direccion": "CC las Ramblas, Kilómetro 10, Cartagena", "coordenadas": [10.519058074115778, -75.46619794203212], "color": "blue", "icono": "hospital"},
     "Centro Médico Colmédica Bocagrande": {"direccion": "Cr 4 # 4 - 78, Cartagena", "coordenadas": [10.398251290207035, -75.55869054232946], "color": "blue", "icono": "hospital"},
     "Centro Médico Colmédica Chía": {"direccion": "Belenus Chía Km 2 vía Chía, Chía", "coordenadas": [4.883582951131957, -74.03724042329465], "color": "blue", "icono": "hospital"},
    "Centro Médico Colmédica Ibagué": {"direccion": "Cra. 5 # 30 - 05, Ibagué", "coordenadas": [4.443406489429007, -75.22333030682144], "color": "blue", "icono": "hospital"},
    "Centro Médico Colmédica Manizales": {"direccion": "C.C. Sancancio, Cr 27 A 66 - 30, Manizales", "coordenadas": [5.054334221451733, -75.48438483625416], "color": "blue", "icono": "hospital"},
    "Centro Médico Colmédica Medellín - El Poblado": {"direccion": "El Poblado, Cr 43B 14 - 44, Medellin", "coordenadas": [6.217569802008974, -75.5599849954142], "color": "blue", "icono": "hospital"},
    "Centro Médico Colmédica Neiva": {"direccion": "Cl 19 # 5a - 50, Neiva", "coordenadas": [2.9372380321218237, -75.28714836532676], "color": "blue", "icono": "hospital"},
    "Centro Médico Colmédica Pereira": {"direccion": "Megacentro, Cl 19 N 12 – 50, Pereira", "coordenadas": [4.805020850357549, -75.68778748692321], "color": "blue", "icono": "hospital"},
    "Centro Médico Colmédica Villavicencio": {"direccion": "Barzal Alto, Cl 32 # 40A – 31, Villavicencio", "coordenadas": [4.1424147251065335, -73.63860592868659], "color": "blue", "icono": "hospital"},
   "Centro Médico Colmédica Yopal": {"direccion": "Clínica Nieves, Cr 21 35 - 68, Yopal", "coordenadas": [5.327695694529845, -72.38637738635713], "color": "blue", "icono": "hospital"},
}

# ---------- FUNCIONES ----------
# <<< CAMBIO: Inicialización del estado de la sesión para las zonas >>>
if 'zonas_emergencia' not in st.session_state:
    st.session_state.zonas_emergencia = []

def remove_accents(input_str):
    """Elimina acentos de los caracteres"""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

@st.cache_data(ttl=3600)
def load_data(uploaded_file):
    """Carga y limpia el archivo CSV optimizado"""
    try:
        if uploaded_file.size > 10 * 1024 * 1024:
            chunks = pd.read_csv(uploaded_file, chunksize=500)
            df = pd.concat(chunks)
        else:
            df = pd.read_csv(uploaded_file)
        
        required_cols = ["Nombre", "Dirección", "Sede asignada", "Teléfono", "Ciudad", "Subproceso", "Criticidad", "Latitud", "Longitud"]
        if not all(col in df.columns for col in required_cols):
            st.error("El archivo no tiene las columnas requeridas")
            return None
        
        df = df.dropna(subset=["Latitud", "Longitud"])
        df["Latitud"] = pd.to_numeric(df["Latitud"], errors="coerce")
        df["Longitud"] = pd.to_numeric(df["Longitud"], errors="coerce")
        df = df.dropna(subset=["Latitud", "Longitud"])
        df = df[(df["Latitud"].between(-90, 90)) & (df["Longitud"].between(-180, 180))]
        
        if len(df) > MAX_MARKERS:
            st.info(f"🔍 Mostrando muestra de {MAX_MARKERS} de {len(df)} registros")
            return df.sample(MAX_MARKERS)
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None

def crear_mapa_base(location=[4.5709, -74.2973], zoom_start=6, tile_provider="MapLibre"):
    """Crea mapa base optimizado"""
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        tiles=TILES[tile_provider]["url"],
        attr=TILES[tile_provider]["attr"],
        control_scale=True,
        prefer_canvas=True
    )
    
    LocateControl(auto_start=False).add_to(m)
    Fullscreen().add_to(m)
    
    Draw(
        export=False, # La exportación directa no es necesaria con nuestro flujo
        position="topleft",
        draw_options={
            'polyline': False,
            'rectangle': True,
            'polygon': True,
            'circle': True,
            'marker': False,
            'circlemarker': False
        }
    ).add_to(m)
    
    return m

def aplicar_filtros(df, ciudad, criticidad, subproceso):
    """Aplica filtros al dataframe"""
    filtered_df = df.copy()
    if ciudad and ciudad != "Todas":
        filtered_df = filtered_df[filtered_df["Ciudad"] == ciudad]
    if criticidad and criticidad != "Todas":
        filtered_df = filtered_df[filtered_df["Criticidad"] == criticidad]
    if subproceso and subproceso != "Todos":
        filtered_df = filtered_df[filtered_df["Subproceso"] == subproceso]
    return filtered_df

def buscar_direccion_colombia(direccion):
    """Geocodificación optimizada"""
    try:
        geolocator = Nominatim(user_agent="continuidad_app", timeout=10, country_codes="co")
        location = geolocator.geocode(f"{direccion}, Colombia", exactly_one=True)
        return location if location and "Colombia" in location.address else None
    except Exception:
        return None

# <<< CAMBIO: Nueva función para analizar múltiples zonas >>>
def analizar_multiples_zonas(lista_zonas, df, sedes_fijas):
    """Genera un reporte consolidado para una lista de zonas, eliminando duplicados."""
    if not lista_zonas:
        return None

    colaboradores_afectados_indices = set()
    sedes_afectadas_nombres = set()

    try:
        for zona_dibujada in lista_zonas:
            if 'geometry' not in zona_dibujada:
                continue

            zona_shape = shape(zona_dibujada['geometry'])

            # Evaluar colaboradores
            for index, row in df.iterrows():
                punto = Point(row["Longitud"], row["Latitud"])
                if zona_shape.contains(punto):
                    colaboradores_afectados_indices.add(index)
            
            # Evaluar sedes
            for nombre, datos in sedes_fijas.items():
                punto = Point(datos["coordenadas"][1], datos["coordenadas"][0])
                if zona_shape.contains(punto):
                    sedes_afectadas_nombres.add(nombre)
        
        # Construir DataFrames finales a partir de los índices y nombres únicos
        df_colaboradores = df.loc[list(colaboradores_afectados_indices)].reset_index(drop=True)
        
        sedes_list = []
        for nombre in sedes_afectadas_nombres:
            datos = sedes_fijas[nombre]
            sedes_list.append({
                "Nombre": nombre,
                "Dirección": datos["direccion"],
                "Coordenadas": datos["coordenadas"]
            })
        df_sedes = pd.DataFrame(sedes_list)

        return {
            "total_colaboradores": len(df_colaboradores),
            "total_sedes": len(df_sedes),
            "colaboradores_afectados": df_colaboradores,
            "sedes_afectadas": df_sedes,
            "zonas": lista_zonas
        }

    except Exception as e:
        st.error(f"Error al generar el reporte multizona: {str(e)}")
        return None

# Las funciones de Vizzu, Excel, PDF y gráficas no necesitan cambios.
# generar_reporte ya no se usará, pero la dejamos por si se necesita en el futuro.
def generar_reporte(zona_dibujada, df, sedes_fijas):
    """Genera reporte para una sola zona (Función legada, usar analizar_multiples_zonas)"""
    return analizar_multiples_zonas([zona_dibujada], df, sedes_fijas)

def mostrar_graficas_vizzu(reporte):
    # ... (Sin cambios) ...
    st.subheader("📊 Estadísticas de la Emergencia")
    col1, col2 = st.columns(2)
    with col1:
        if not reporte["colaboradores_afectados"].empty:
            st.write("#### Distribución por Criticidad")
            df_criticidad = reporte["colaboradores_afectados"]
            data = Data()
            data.add_df(df_criticidad)
            chart = VizzuChart(key="vizzu_criticidad", height=400)
            chart.animate(data)
            chart.animate(Config({"channels": {"color": {"set": ["Criticidad"]}, "size": {"attach": ["count()"]},}, "title": "Colaboradores por Nivel de Criticidad", "coordSystem": "polar", "geometry": "area"}), Style({"title": {"fontSize": 18}, "plot": {"marker": {"colorPalette": "#4A90E2FF #50E3C2FF #F5A623FF #D0021BFF #BD10E0FF"}}}))
    with col2:
        if not reporte["colaboradores_afectados"].empty:
            st.write("#### Subprocesos Afectados por colaboradores")
            df_subproceso = reporte["colaboradores_afectados"]['Subproceso'].value_counts().nlargest(5).reset_index()
            df_subproceso.columns = ['Subproceso', 'Cantidad']
            data_sub = Data()
            data_sub.add_df(df_subproceso)
            chart_sub = VizzuChart(key="vizzu_subproceso", height=400)
            chart_sub.animate(data_sub)
            chart_sub.animate(Config({"x": "Cantidad", "y": "Subproceso", "title": "Top Subprocesos Afectados", "label": "Cantidad", "color": "Subproceso"}), Style({"title": {"fontSize": 18}, "plot": {"marker": {"colorPalette": "#50E3C2FF #4A90E2FF #F5A623FF #D0021BFF #BD10E0FF"}}}))

def generar_excel_reporte(reporte, tipo_evento, descripcion):
    # ... (Sin cambios) ...
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        resumen_data = {"Parámetro": ["Tipo de Evento", "Descripción", "Fecha del Reporte", "Total Colaboradores Afectados", "Total Sedes Afectadas"], "Valor": [tipo_evento, descripcion, datetime.now().strftime('%Y-%m-%d %H:%M'), reporte['total_colaboradores'], reporte['total_sedes']]}
        pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)
        if not reporte["sedes_afectadas"].empty: reporte["sedes_afectadas"].to_excel(writer, sheet_name='Sedes Afectadas', index=False)
        if not reporte["colaboradores_afectados"].empty: reporte["colaboradores_afectados"].to_excel(writer, sheet_name='Colaboradores Afectados', index=False)
    return output.getvalue()

def generar_graficas_pdf(reporte):
    """Genera gráficas optimizadas para PDF con números enteros y mejor diseño."""
    figuras = []
    colores_profesionales = ['#4A90E2', '#50E3C2', '#F5A623', '#D0021B', '#BD10E0', '#7ED321', '#9013FE']

    # Gráfica 1: Sedes Afectadas (Barras Verticales)
    if not reporte["sedes_afectadas"].empty:
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        datos = reporte["sedes_afectadas"]["Nombre"].value_counts()
        datos.plot(kind='bar', ax=ax1, color=colores_profesionales[0])
        ax1.set_title('Sedes Afectadas', fontsize=14, weight='bold')
        ax1.tick_params(axis='x', rotation=30, labelsize=10)
        plt.setp(ax1.get_xticklabels(), ha="right", rotation_mode="anchor")
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # <<< CAMBIO: Forzar el eje Y a usar solo números enteros >>>
        ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax1.set_ylim(bottom=0) # Asegurar que el eje Y comience en 0

        plt.tight_layout()
        figuras.append(fig1)

    # Gráfica 2: Distribución por Criticidad (Gráfico de Torta/Pie)
    if not reporte["colaboradores_afectados"].empty:
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        datos = reporte["colaboradores_afectados"]["Criticidad"].value_counts()
        
        # <<< CAMBIO: Crear etiquetas que incluyan el conteo absoluto >>>
        # Ejemplo: "Crítico (15)"
        labels_con_conteo = [f'{index}\n({value} colaboradores)' for index, value in datos.items()]
        
        # <<< CAMBIO: Formatear el porcentaje a un número entero (ej. 45%) >>>
        ax2.pie(datos, labels=labels_con_conteo, autopct='%1.0f%%', 
                startangle=90, colors=colores_profesionales,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
                pctdistance=0.8, labeldistance=1.05) # Ajustar distancias si es necesario
                
        ax2.set_title('Distribución por Criticidad de Colaboradores', fontsize=14, weight='bold')
        ax2.axis('equal')
        plt.tight_layout()
        figuras.append(fig2)

    # Gráfica 3: Top 5 Subprocesos Afectados (Barras Horizontales)
    if not reporte["colaboradores_afectados"].empty:
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        datos = reporte["colaboradores_afectados"]["Subproceso"].value_counts().head(5)
        datos.sort_values().plot(kind='barh', ax=ax3, color=colores_profesionales)
        ax3.set_title('Top 5 Subprocesos Afectados', fontsize=14, weight='bold')
        ax3.set_xlabel('Número de Colaboradores', fontsize=10)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.grid(axis='x', linestyle='--', alpha=0.7)
        
        # <<< CAMBIO: Forzar el eje X a usar solo números enteros >>>
        ax3.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax3.set_xlim(left=0) # Asegurar que el eje X comience en 0

        plt.tight_layout()
        figuras.append(fig3)

    return figuras

def crear_pdf(reporte, tipo_evento, descripcion_emergencia=""):
    """Crea un PDF con el reporte de emergencia"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        try:
            pdf.image("assets/logo_colmedica.png", x=10, y=8, w=40)
        except FileNotFoundError:
            st.warning("Advertencia: No se encontró el archivo del logo. El PDF se generará sin él.")
        
        pdf.set_font("Arial", size=12)
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt="REPORTE DE EMERGENCIA - COLMÉDICA", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Información del Evento", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, txt=f"Tipo de evento: {remove_accents(tipo_evento)}", ln=1)
        
        descripcion_simple = remove_accents(descripcion_emergencia)
        pdf.multi_cell(0, 8, txt=f"Descripción: {descripcion_simple}")
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Resumen de la Emergencia", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, txt=f"Total colaboradores afectados: {reporte['total_colaboradores']}", ln=1)
        pdf.cell(0, 8, txt=f"Total sedes afectadas: {reporte['total_sedes']}", ln=1)
        
        if 'emergencia_location' in st.session_state and 'address' in st.session_state.emergencia_location:
            ubicacion_simple = remove_accents(st.session_state.emergencia_location['address'])
            pdf.cell(0, 8, txt=f"Ubicación: {ubicacion_simple}", ln=1)
        pdf.ln(10)
        
        # --- Gráficas (sin cambios) ---
        figuras_pdf = generar_graficas_pdf(reporte)
        temp_files = []
        try:
            for fig in figuras_pdf:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                    fig.savefig(tmpfile.name, dpi=150, bbox_inches='tight')
                    temp_files.append(tmpfile.name)
                plt.close(fig)
            
            for temp_file in temp_files:
                pdf.add_page()
                pdf.image(temp_file, x=10, w=190)
        finally:
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        # <<< --- INICIO DEL CAMBIO: TABLA DE SEDES AFECTADAS --- >>>
        if not reporte["sedes_afectadas"].empty:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="Sedes Afectadas", ln=1)
            pdf.set_font("Arial", 'B', 10) # Fuente en negrita para cabeceras
            
            # Definir anchos de columna (total debe ser ~190 para A4)
            col_width_nombre = 70
            col_width_direccion = 120
            
            # Cabecera de la tabla
            pdf.set_fill_color(200, 220, 255) # Color de fondo azul claro
            pdf.cell(col_width_nombre, 8, "Nombre Sede", 1, 0, 'C', True)
            pdf.cell(col_width_direccion, 8, "Dirección", 1, 1, 'C', True)
            
            # Contenido de la tabla
            pdf.set_font("Arial", size=9) # Fuente normal para el contenido
            pdf.set_fill_color(255, 255, 255) # Resetear color de fondo
            for _, row in reporte["sedes_afectadas"].iterrows():
                # Limpiamos y cortamos el texto para que quepa en la celda
                nombre_simple = remove_accents(row['Nombre'])[:45]
                direccion_simple = remove_accents(row['Dirección'])[:75]
                
                pdf.cell(col_width_nombre, 8, txt=nombre_simple, border=1, align='L')
                pdf.cell(col_width_direccion, 8, txt=direccion_simple, border=1, align='L', ln=1)
        # <<< --- FIN DEL CAMBIO --- >>>

        # --- Tabla de Colaboradores (sin cambios) ---
        if not reporte["colaboradores_afectados"].empty:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="Colaboradores Afectados (primeros 50)", ln=1)
            pdf.set_font("Arial", 'B', 8)
            
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(60, 6, "Nombre", 1, 0, 'C', True)
            pdf.cell(50, 6, "Sede", 1, 0, 'C', True)
            pdf.cell(50, 6, "Subproceso", 1, 0, 'C', True)
            pdf.cell(30, 6, "Criticidad", 1, 1, 'C', True)
            
            pdf.set_font("Arial", size=8)
            pdf.set_fill_color(255, 255, 255)
            for _, row in reporte["colaboradores_afectados"].head(50).iterrows():
                nombre_simple = remove_accents(row['Nombre'])[:35]
                sede_simple = remove_accents(row['Sede asignada'])[:30]
                subproceso_simple = remove_accents(row['Subproceso'])[:30]
                
                pdf.cell(60, 6, txt=nombre_simple, border=1)
                pdf.cell(50, 6, txt=sede_simple, border=1)
                pdf.cell(50, 6, txt=subproceso_simple, border=1)
                pdf.cell(30, 6, txt=str(row['Criticidad']), border=1, ln=1)
        
        # --- Generación del archivo (sin cambios) ---
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            pdf.output(tmp_pdf.name)
            tmp_pdf.seek(0)
            pdf_bytes = tmp_pdf.read()
        
        # Eliminar el archivo temporal del disco
        try:
            os.unlink(tmp_pdf.name)
        except Exception as e:
            st.warning(f"No se pudo eliminar el archivo PDF temporal: {e}")

        return pdf_bytes
    
    except Exception as e:
        st.error(f"Error al generar el PDF: {str(e)}")
        return None

def get_table_download_link(df, filename="reporte.csv"):
    """Genera un enlace para descargar un dataframe como CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Descargar archivo CSV</a>'
    return href

# ---------- INTERFAZ ----------
with st.sidebar:
    try:
        st.image("assets/logo_colmedica.png", use_container_width=True)
    except FileNotFoundError:
        st.sidebar.title("Sistema de Continuidad")
    
    st.header("⚙️ Configuración")
    tile_provider = st.selectbox("Seleccionar tipo de mapa", list(TILES.keys()), index=0)
    
    st.header("🔍 Filtros")
    archivo = st.file_uploader("📄 Subir CSV de colaboradores", type="csv")
    
    ciudad, criticidad, subproceso = None, None, None
    if archivo:
        if 'df' not in st.session_state or st.session_state.get('uploaded_filename') != archivo.name:
            with st.spinner('Procesando archivo, por favor espere...'):
                st.session_state.df = load_data(archivo)
                st.session_state.uploaded_filename = archivo.name

        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            ciudades = ["Todas"] + sorted(df["Ciudad"].unique().tolist())
            criticidades = ["Todas"] + sorted(df["Criticidad"].astype(str).unique().tolist())
            subprocesos = ["Todos"] + sorted(df["Subproceso"].unique().tolist())
            ciudad = st.selectbox("Ciudad", ciudades, index=0)
            criticidad = st.selectbox("Criticidad", criticidades, index=0)
            subproceso = st.selectbox("Subproceso", subprocesos, index=0)

    # <<< CAMBIO: Lógica de la barra lateral modificada >>>
    st.header("📍 Emergencia por Dirección")
    with st.expander("BUSCAR DIRECCIÓN EN COLOMBIA", expanded=True):
        direccion = st.text_input(label="Buscar dirección:", placeholder="Ej: Carrera 15 #32-41, Bogotá", key="direccion_input")
        
        if st.button("🗺️ Encontrar en el mapa"):
            if direccion:
                with st.spinner("Buscando..."):
                    location = buscar_direccion_colombia(direccion)
                    if location:
                        st.session_state.emergencia_location = {"coords": [location.latitude, location.longitude], "address": location.address}
                        st.success(f"✅ Ubicación encontrada!")
                    else:
                        st.error("Dirección no encontrada")

    # Botón para añadir la dirección buscada como una zona de emergencia
    if 'emergencia_location' in st.session_state:
        st.info(f"📍 **Ubicación Marcada:**\n{st.session_state.emergencia_location['address']}")
        if st.button("➕ Añadir esta dirección como zona de emergencia"):
            punto_emergencia = Point(st.session_state.emergencia_location['coords'][1], st.session_state.emergencia_location['coords'][0])
            # Crea un círculo con un radio de ~500 metros (0.005 grados)
            zona_circular = punto_emergencia.buffer(0.005)
            
            # Convierte la zona a un formato compatible (GeoJSON-like)
            zona_para_anadir = {'geometry': mapping(zona_circular)}
            st.session_state.zonas_emergencia.append(zona_para_anadir)
            st.success("Zona circular añadida al análisis.")
            # Borra la ubicación para no añadirla múltiples veces por error
            del st.session_state.emergencia_location


# --- MAPA Y LÓGICA PRINCIPAL ---
m = crear_mapa_base(tile_provider=tile_provider)

# Mostrar sedes fijas
for nombre, datos in SEDES_FIJAS.items():
    folium.Marker(
        location=datos["coordenadas"],
        popup=f"<b>{nombre}</b><br>{datos['direccion']}",
        icon=folium.Icon(color=datos["color"], icon=datos["icono"], prefix='fa')
    ).add_to(m)

# <<< CAMBIO: Visualizar las zonas ya guardadas >>>
if st.session_state.zonas_emergencia:
    for i, zona in enumerate(st.session_state.zonas_emergencia):
        folium.GeoJson(
            zona['geometry'],
            style_function=lambda x: {'fillColor': 'red', 'color': 'black', 'weight': 2.5, 'fillOpacity': 0.4},
            tooltip=f"Zona de Emergencia #{i+1}"
        ).add_to(m)

# Procesar archivo subido y mostrar colaboradores
if 'df' in st.session_state and st.session_state.df is not None:
    df = st.session_state.df
    df_filtrado = aplicar_filtros(df, ciudad, criticidad, subproceso)
    
    marker_cluster = MarkerCluster(name="Colaboradores", max_cluster_radius=50, disable_clustering_at_zoom=14).add_to(m)
    
    # 1. Define el mapa de colores EXACTO para tus niveles de criticidad.
    #    (Usando 'orange' para Esencial y 'green' para De Apoyo)
    #    Para 'Importante' (amarillo), vamos a usar 'beige' que es un color soportado.
    mapa_colores_criticidad = {
        'Critico': 'red',       # Nivel 'Critico' -> Rojo
        'Escencial': 'orange',  # Nivel 'Escencial' -> Naranja
        'Importante': 'beige',  # Nivel 'Importante' -> Amarillo/Beige
        'DeApoyo': 'green'     # Nivel 'De Apoyo' -> Verde
    }
    
    
    for _, row in df_filtrado.iterrows():
        criticidad_valor = str(row['Criticidad']).strip()
        color_marcador = mapa_colores_criticidad.get(criticidad_valor, 'gray')

        folium.Marker(
            location=[row["Latitud"], row["Longitud"]],
            popup=f"<b>{row['Nombre']}</b><br>Sede: {row['Sede asignada']}<br>Subproceso: {row['Subproceso']}<br>Criticidad: {row['Criticidad']}",
            icon=folium.Icon(icon='user', prefix='fa', color=color_marcador)
        ).add_to(marker_cluster)
    
    # Centrar mapa en la última ubicación buscada
    if 'emergencia_location' in st.session_state:
        m.location = st.session_state.emergencia_location["coords"]
        m.zoom_start = 15

# Mostrar mapa
map_data = st_folium(m, width=1200, height=600, key="mapa_principal")


# <<< CAMBIO: Nueva sección para gestionar y analizar las zonas >>>
st.header("Zonas de Emergencia")
col1, col2, col3 = st.columns([2, 2, 1])

# Columna 1: Añadir zona dibujada
with col1:
    # Guardar el último dibujo en el estado de la sesión para que persista
    if map_data.get("last_active_drawing"):
        st.session_state.last_drawn = map_data["last_active_drawing"]

    if 'last_drawn' in st.session_state and st.session_state.last_drawn:
        st.info("Se ha detectado una nueva zona dibujada en el mapa.")
        if st.button("➕ Añadir Zona Dibujada", use_container_width=True):
            st.session_state.zonas_emergencia.append(st.session_state.last_drawn)
            del st.session_state.last_drawn  # Limpiar el dibujo temporal
            st.success("¡Zona añadida! Puedes dibujar otra o analizar las zonas marcadas.")
            st.rerun()

# Columna 2: Analizar todas las zonas marcadas
with col2:
    if st.session_state.zonas_emergencia:
        num_zonas = len(st.session_state.zonas_emergencia)
        st.markdown(f"**Tiene {num_zonas} zona(s) de emergencia marcada(s).**")
        if st.button("🔬 Analizar Zonas Marcadas", type="primary", use_container_width=True):
            if 'df' in st.session_state and st.session_state.df is not None:
                with st.spinner("Analizando todas las zonas..."):
                    df_filtrado_analisis = aplicar_filtros(st.session_state.df, ciudad, criticidad, subproceso)
                    reporte = analizar_multiples_zonas(st.session_state.zonas_emergencia, df_filtrado_analisis, SEDES_FIJAS)
                    if reporte:
                        st.session_state.reporte_emergencia = reporte
                        st.success(f"Análisis completo: {reporte['total_colaboradores']} colaboradores y {reporte['total_sedes']} sedes afectadas en total.")
                    else:
                        st.error("No se pudo generar el reporte.")
            else:
                st.warning("Por favor, cargue el archivo CSV de colaboradores primero.")

# Columna 3: Limpiar zonas
with col3:
    if st.session_state.zonas_emergencia:
        if st.button("🗑️ Limpiar Zonas Marcadas", use_container_width=True):
            st.session_state.zonas_emergencia = []
            if 'reporte_emergencia' in st.session_state:
                del st.session_state.reporte_emergencia
            st.info("Todas las zonas han sido eliminadas.")
            st.rerun()

st.markdown("---")


# Mostrar reporte si existe
if 'reporte_emergencia' in st.session_state:
    reporte = st.session_state.reporte_emergencia
    
    st.header("📝 Reporte de Emergencia Consolidado")
    
    tipo_evento = st.selectbox(
        "Tipo de Emergencia",
        options=["Evento Social (Marchas, Protestas)", "Evento Climático (Inundaciones, Derrumbe)", "Evento de Tráfico (Accidentes, Bloqueos)", "Falla de Infraestructura", "Otro"],
        index=0
    )
    descripcion_emergencia = st.text_area(
        "✍️ Describa el evento de emergencia:",
        placeholder="Ej: Múltiples zonas afectadas por inundaciones en Bogotá...",
        height=100
    )
    
    col1, col2 = st.columns(2)
    col1.metric("Total Colaboradores Afectados (Únicos)", reporte["total_colaboradores"])
    col2.metric("Total Sedes Afectadas (Únicas)", reporte["total_sedes"])
    
    mostrar_graficas_vizzu(reporte)
    
    if not reporte["sedes_afectadas"].empty:
        st.subheader("🏥 Sedes Afectadas")
        st.dataframe(reporte["sedes_afectadas"][["Nombre", "Dirección"]], use_container_width=True, height=200)
    
    if not reporte["colaboradores_afectados"].empty:
        st.subheader("👥 Colaboradores Afectados")
        st.dataframe(reporte["colaboradores_afectados"][["Nombre", "Sede asignada", "Subproceso", "Criticidad"]], use_container_width=True, height=300)
    
    st.subheader("📤 Exportar Reporte Completo")
    col_pdf, col_excel = st.columns(2)

    with col_pdf:
        if st.button("🖨️ Generar PDF del Reporte", key="gen_pdf_btn"):
            with st.spinner("Generando PDF..."):
                pdf_bytes = crear_pdf(reporte, tipo_evento, descripcion_emergencia)
                if pdf_bytes:
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"reporte_emergencia_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="download_pdf"
                    )

    with col_excel:
        if st.button("📄 Generar Excel del Reporte", key="gen_excel_btn"):
            with st.spinner("Generando Excel..."):
                excel_bytes = generar_excel_reporte(reporte, tipo_evento, descripcion_emergencia)
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_bytes,
                    file_name=f"reporte_emergencia_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )

    if not reporte["colaboradores_afectados"].empty:
        st.markdown("---")
        st.markdown("##### Opcional: Descarga Rápida (Solo Colaboradores en CSV)")
        st.markdown(get_table_download_link(reporte["colaboradores_afectados"], "colaboradores_afectados.csv"), unsafe_allow_html=True)        
# Dashboard general
if 'df' in st.session_state and st.session_state.df is not None:
    df = st.session_state.df
    st.subheader("📊 Dashboard General (Datos Cargados)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Colaboradores", len(df))
    col2.metric("Sedes Únicas", df["Sede asignada"].nunique())
    col3.metric("Ciudades", df["Ciudad"].nunique())
    
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    
    df["Ciudad"].value_counts().head(5).plot(kind='bar', ax=ax[0], color='#4A90E2')
    ax[0].set_title('Top 5 Ciudades por # de Colaboradores')
    ax[0].tick_params(axis='x', rotation=45)

    df["Sede asignada"].value_counts().head(5).plot(kind='bar', ax=ax[1], color='#50E3C2')
    ax[1].set_title('Top 5 Sedes por # de Colaboradores')
    ax[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    st.pyplot(fig)