import streamlit as st
import pandas as pd
import altair as alt
from etl import find_header_and_data, load_data, process_events

st.set_page_config(page_title="Monitor de Lectura Telepase", layout="wide")

# --- Interfaz ---
st.title("📡 Sistema de Monitoreo Telepase")

uploaded_file = st.file_uploader("Cargar archivo", type=['csv', 'xls', 'xlsx'])

if uploaded_file is not None:
    df_clean = load_data(uploaded_file)
    
    if df_clean is not None:
        df_processed = process_events(df_clean)
        
        if not df_processed.empty:
            
            # --- FILTRO POR VÍA (Sidebar) ---
            st.sidebar.header("Filtros")
            vias_disponibles = df_processed['Vía'].dropna().unique().tolist()
            
            vias_seleccionadas = st.sidebar.multiselect(
                "Selecciona la Vía a monitorear:",
                options=vias_disponibles,
                default=vias_disponibles,
                help="Si deseleccionas todas, no se mostrarán datos."
            )
            
            # Aplicar filtro
            df_filtrado = df_processed[df_processed['Vía'].isin(vias_seleccionadas)]
            
            if df_filtrado.empty:
                st.warning("No hay datos para las Vías seleccionadas. Por favor, marca al menos una Vía en el menú izquierdo.")
            else:
                counts = df_filtrado['Estado'].value_counts()
                total = len(df_filtrado)
                reads = counts.get("Leído Correctamente (TAG)", 0)
                manuals = counts.get("Manual (No Leído)", 0)
                effectiveness = (reads / total * 100) if total > 0 else 0
                
                st.divider()
                st.markdown(f"### 📊 Métricas para las vías: {', '.join(map(str, vias_seleccionadas))}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Vehículos", total)
                c2.metric("Lecturas OK", reads)
                c3.metric("Fallo (Manual)", manuals)
                c4.metric("Efectividad", f"{effectiveness:.1f}%")
                st.divider()
                
                col_chart, col_data = st.columns([1, 2])
                
                with col_chart:
                    chart_data = pd.DataFrame({'Estado': counts.index, 'Cantidad': counts.values})
                    
                    # Definimos exactamente qué color va con qué estado
                    color_scale = alt.Scale(
                        domain=["Leído Correctamente (TAG)", "Manual (No Leído)", "Otro (Violación/Exento)"],
                        range=["#648040", "#C0C0C0", "#FFD700"]  
                    )
                    
                    base = alt.Chart(chart_data).encode(theta=alt.Theta("Cantidad", stack=True))
                    pie = base.mark_arc(innerRadius=60).encode(
                        color=alt.Color("Estado", scale=color_scale, legend=alt.Legend(title="Estados")),
                        order=alt.Order("Cantidad", sort="descending"),
                        tooltip=["Estado", "Cantidad"]
                    )
                    st.altair_chart(pie, theme="streamlit")
                    
                with col_data:
                    # Mostrar la tabla con el nuevo orden de columnas
                    st.dataframe(
                        df_filtrado[['Hora', 'Vía', 'Patente', 'TAG', 'Sentido', 'Tránsito', 'Estado']], 
                        width='stretch', 
                        height=400
                    )