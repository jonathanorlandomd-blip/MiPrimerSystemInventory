import streamlit as st
import pandas as pd
import os

# 1. Configuración de la página
st.set_page_config(page_title="Inventario de Poleras", layout="wide")
st.title("👕 Gestión de Inventario de Poleras")

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
columnas_tallas = [col for col in df.columns if col not in ['Modelo', 'Imagen']]
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
            ruta_img = os.path.join("imagenes", str(row['Imagen']))
            if os.path.exists(ruta_img):
                st.image(ruta_img, width=200)
            else:
                st.write("🖼️ Sin imagen")
        
        # Columna 2: Información y Tallas
        with c2:
            st.subheader(row['Modelo'])
            
            # Mostramos las tallas como un pequeño dataframe transpuesto para que se vea limpio
            tallas_row = row[columnas_tallas].to_frame().T
            st.dataframe(tallas_row, hide_index=True)
            
            # Stock total de este modelo específico
            stock_modelo = row[columnas_tallas].sum()
            
            # Alerta visual de stock bajo
            if stock_modelo < 5:
                st.warning(f"⚠️ Stock bajo: Quedan solo {int(stock_modelo)} unidades.")
            else:
                st.success(f"✅ Stock total modelo: {int(stock_modelo)}")
        
        st.divider()

# 6. Tabla completa cruda (opcional, para ver todo junto)
with st.expander("Ver tabla de datos completa"):
    st.dataframe(df_filtrado)