import streamlit as st
import pandas as pd
import os
from gspread_pandas import Spread, Client
import gspread

# 1. Configuración de la página
st.set_page_config(page_title="Inventario de Poleras", layout="wide")
st.title("👕 Gestión de Inventario de Poleras")

# --- CONEXIÓN A GOOGLE SHEETS (OPTIMIZADA CON CACHING) ---
# Usamos @st.cache_resource para que la conexión se establezca una sola vez.
@st.cache_resource
def get_gsheet_client():
    """Se conecta a Google Sheets usando las credenciales de los secrets y devuelve el cliente."""
    # Usamos gspread para la autenticación
    creds = st.secrets["gcp_service_account"].to_dict()
    # La private_key en los secrets de Streamlit a veces pierde los saltos de línea.
    # Los reconstruimos para asegurar que la autenticación funcione.
    creds['private_key'] = creds['private_key'].replace('\\n', '\n')
    
    sa = gspread.service_account_from_dict(creds)
    return sa

# Usamos @st.cache_data para cargar los datos y guardarlos en caché.
# El TTL (time-to-live) de 600 segundos (10 minutos) hace que los datos se recarguen
# desde la fuente cada 10 minutos, para no sobrecargar la API.
@st.cache_data(ttl=600)
def load_data(_gsheet_client):
    """Carga los datos desde la hoja de Google y los devuelve como un DataFrame."""
    # Usamos gspread-pandas para interactuar con la hoja
    spread = Spread(st.secrets["gcp_service_account"]["sheet_name"], client=_gsheet_client)
    df = spread.sheet_to_df(index=False, sheet='Sheet1')
    df = df.fillna(0)
    return df

# --- CARGA Y GUARDADO DE DATOS ---
try:
    client = get_gsheet_client()
    df = load_data(client)

    def guardar_datos(dataframe):
        """Guarda el DataFrame en la hoja de cálculo de Google."""
        spread = Spread(st.secrets["gcp_service_account"]["sheet_name"], client=client)
        spread.df_to_sheet(dataframe, index=False, sheet='Sheet1', replace=True)
        st.cache_data.clear() # Limpiamos la caché de datos para que se recarguen en el rerun

except Exception as e:
    st.error(f"Error al cargar o conectar con Google Sheets: {e}")
    st.stop()

# 3. Barra lateral (Sidebar) para Filtros y Resumen
st.sidebar.header("🔍 Filtros y Resumen")

# Filtro por nombre de modelo
busqueda = st.sidebar.text_input("Buscar modelo:")
if busqueda:
    df_filtrado = df[df['Modelo'].str.contains(busqueda, case=False, na=False)]
else:
    df_filtrado = df

# 4. Métricas Generales (Totales)
# Identificamos las columnas que son numéricas (las tallas)
columnas_tallas = [col for col in df_filtrado.columns if col not in ['Modelo', 'Imagen']]
total_prendas = df_filtrado[columnas_tallas].sum().sum()
total_modelos = len(df_filtrado)

col1, col2 = st.sidebar.columns(2)
col1.metric("Total Prendas", int(total_prendas))
col2.metric("Modelos Visibles", total_modelos)

# 5. Visualización del Inventario
st.divider()

# Mostrar cada producto
for index, row in df_filtrado.iterrows():
    with st.container():
        c1, c2 = st.columns([1, 3])
        
        # Columna 1: Imagen
        with c1:
            # La ruta ya viene completa en el CSV (ej: "imagenes/foto.png")
            # No es necesario usar os.path.join con la carpeta "imagenes"
            ruta_img = str(row['Imagen'])
            if os.path.exists(ruta_img):
                st.image(ruta_img, width=200)
            else:
                st.write("🖼️ Sin imagen")
        
        # Columna 2: Información y Tallas
        with c2:
            st.subheader(row['Modelo'])
            
            # --- LÓGICA PARA MOSTRAR TALLAS CORRECTAS ---
            # Definimos los dos grupos de tallas que existen en el CSV
            tallas_adulto = ['S', 'M', 'L', 'XL', 'XXL']
            tallas_nino = ['Talla 16', 'Talla 18', 'Talla 20', 'Talla 22', 'Talla 24', 'Talla 26', 'Talla 28']
            
            # Decidimos qué grupo de tallas mostrar basado en el nombre del modelo
            if 'Short + Polera U' in row['Modelo']:
                tallas_a_mostrar = tallas_nino
            else:
                tallas_a_mostrar = tallas_adulto

            # --- SECCIÓN INTERACTIVA DE TALLAS ---
            # Usamos la lista de tallas correcta ('tallas_a_mostrar')
            num_columnas_layout = 4 # Puedes ajustar este número (ej. 3 o 5)
            layout_cols = st.columns(num_columnas_layout)
            
            for i, talla in enumerate(tallas_a_mostrar):
                # Asignamos cada talla a una de las columnas de layout
                if not talla in row: continue # Seguridad por si una talla no existe en el df

                col_actual = layout_cols[i % num_columnas_layout]
                with col_actual:
                    # Usamos un contenedor con borde para crear la "casilla"
                    with st.container(border=True):
                        stock_actual = int(row[talla])
                        
                        # --- LÓGICA PARA ETIQUETA DE TALLA DE NIÑO ---
                        etiqueta_talla = talla
                        if talla in tallas_nino:
                            # Extraemos el número de la talla (ej. 16 de "Talla 16")
                            numero_talla = int(talla.split(' ')[1])
                            # Calculamos el número para el paréntesis: (16-16)+4=4, (18-16)+4=6, etc.
                            numero_adicional = (numero_talla - 16) + 4
                            etiqueta_talla = f"{talla} ({numero_adicional})"
                        
                        # Usamos HTML en markdown para centrar el texto
                        st.markdown(f"<p style='text-align: center; font-weight: bold;'>{etiqueta_talla}</p>", unsafe_allow_html=True)
                        
                        # Reemplazamos st.metric con markdown para centrar el número de stock
                        st.markdown(f"<h2 style='text-align: center;'>{stock_actual}</h2>", unsafe_allow_html=True)
                        
                        # Columnas para los botones, para que estén uno al lado del otro
                        btn_col1, btn_col2 = st.columns(2)
                        
                        if btn_col1.button("➕", key=f"plus-{index}-{talla}", use_container_width=True):
                            df.loc[index, talla] = stock_actual + 1
                            guardar_datos(df)
                            st.rerun()
                        
                        if btn_col2.button("➖", key=f"minus-{index}-{talla}", use_container_width=True):
                            if stock_actual > 0:
                                df.loc[index, talla] = stock_actual - 1
                                guardar_datos(df)
                                st.rerun()
            
            # Stock total de este modelo específico
            stock_modelo = row[tallas_a_mostrar].sum()
            st.divider()
            
            # Alerta visual de stock bajo (se mantiene igual)
            st.metric("Stock Total del Modelo", int(stock_modelo))
        
        st.divider()

# 6. Tabla completa cruda (opcional, para ver todo junto)
with st.expander("Ver tabla de datos completa"):
    st.dataframe(df_filtrado)