import streamlit as st
import pandas as pd
import os
import time

# 1. Configuración de la página
st.set_page_config(page_title="Inventario de Poleras", layout="wide")
st.title("👕 Gestión de Inventario de Poleras")

# --- FUNCIÓN PARA GUARDAR DATOS ---
# Es una buena práctica tener una función para guardar, así evitamos repetir código.
def guardar_datos(dataframe):
    """Guarda el DataFrame en el archivo CSV."""
    dataframe.to_csv("inventario.csv", index=False)


# 2. Cargar datos
# Asegúrate de que tu archivo se llame 'inventario.csv' y esté limpio como indicamos
try:
    df = pd.read_csv("inventario.csv") # O usa pd.read_excel("inventario.xlsx")
    
    # Rellenar espacios vacíos con 0 para poder sumar
    df = df.fillna(0)
except FileNotFoundError:
    st.error("No se encontró el archivo de inventario. Asegúrate de cargarlo.")
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
            if 'Short + Polera U' in row['Modelo'] or 'Short + Polera CC' in row['Modelo']:
                tallas_a_mostrar = tallas_nino
            else:
                tallas_a_mostrar = tallas_adulto

            # --- SECCIÓN INTERACTIVA DE TALLAS ---
            # --- LÓGICA DE LAYOUT MEJORADA PARA RESPONSIVIDAD MÓVIL ---
            # Procesamos las tallas en grupos (filas) para mantener el orden en cualquier dispositivo.
            tallas_por_fila = 3
            grupos_de_tallas = [tallas_a_mostrar[i:i + tallas_por_fila] for i in range(0, len(tallas_a_mostrar), tallas_por_fila)]

            for grupo in grupos_de_tallas:
                # Creamos una nueva fila de columnas para cada grupo de tallas
                cols = st.columns(tallas_por_fila)
                for col_index, talla in enumerate(grupo):
                    if not talla in row: continue # Seguridad por si una talla no existe en el df

                    with cols[col_index]:
                        # Usamos un contenedor con borde para crear la "casilla"
                        with st.container(border=True):
                            stock_actual = int(row[talla])
                            
                            etiqueta_talla = talla
                            # Lógica para formatear etiquetas de niño (se mantiene igual)
                            if tallas_a_mostrar == tallas_nino:
                                numero_talla = int(talla.split(' ')[1])
                                etiqueta_talla = f"Talla {numero_talla}"
                            
                            # Elementos de la interfaz (se mantienen igual)
                            # SOLUCIÓN: Usar st.empty() para crear contenedores únicos y evitar bugs de renderizado en móvil.
                            # st.markdown no acepta el argumento 'key', por lo que esta es la forma correcta.
                            label_placeholder = st.empty()
                            stock_placeholder = st.empty()
                            label_placeholder.markdown(f"<p style='text-align: center; font-weight: bold;'>{etiqueta_talla}</p>", unsafe_allow_html=True)
                            stock_placeholder.markdown(f"<h2 style='text-align: center;'>{stock_actual}</h2>", unsafe_allow_html=True)
                            
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
            
            # Alerta visual de stock bajo (se mantiene igual)
            st.metric("Stock Total del Modelo", int(stock_modelo))

        st.divider()

# 6. Tabla completa cruda (opcional, para ver todo junto)
with st.expander("Ver tabla de datos completa"):
    st.dataframe(df_filtrado)