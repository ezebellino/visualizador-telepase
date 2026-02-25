import streamlit as st
import pandas as pd
import altair as alt
import re # Librería para extraer texto (Patentes)

st.set_page_config(page_title="Monitor de Lectura Telepase", layout="wide")

def find_header_and_data(df_raw):
    # (El mismo código que ya tenías para encontrar la cabecera)
    header_idx = None
    for i, row in df_raw.head(50).iterrows():
        row_text = " ".join(row.astype(str).str.lower().values)
        if "hora" in row_text and ("vía" in row_text or "via" in row_text or "descripción" in row_text):
            header_idx = i
            break
            
    if header_idx is None: return None
    df_raw.columns = df_raw.iloc[header_idx]
    return df_raw[header_idx + 1:].reset_index(drop=True)

def load_data(uploaded_file):
    # (El mismo código de carga que ya tenías)
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df = None
    try:
        if file_extension in ['xls', 'xlsx']:
            engine = 'xlrd' if file_extension == 'xls' else 'openpyxl'
            try:
                df = pd.read_excel(uploaded_file, header=None, engine=engine)
            except:
                df = pd.read_excel(uploaded_file, header=None)
        else:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, header=None, encoding=encoding, sep=None, engine='python')
                    break
                except: continue
        if df is None: return None
        return find_header_and_data(df)
    except: return None

def extract_patente(obs):
    """Extrae la patente de la columna Observación usando Regex"""
    if pd.isna(obs): return "N/A"
    # Busca la palabra 'Patente:', espacios opcionales, y captura las letras/números
    match = re.search(r'Patente:\s*([A-Z0-9]+)', str(obs), re.IGNORECASE)
    return match.group(1) if match else "N/A"

def extract_tag(obs):
    """Extrae el número de TAG de la columna Observación usando Regex"""
    if pd.isna(obs): return "N/A"
    # Busca la palabra 'Número:' o 'Tag:', admite espacios, y captura el código alfanumérico
    match = re.search(r'(?:Número|Tag):\s*([A-Z0-9]+)', str(obs), re.IGNORECASE)
    return match.group(1) if match else "N/A"

def process_events(df):
    processed_rows = []
    manual_pending = False
    
    df.columns = df.columns.astype(str).str.strip()
    
    # Normalizar nombres de columnas
    col_map = {c: c for c in df.columns}
    for c in df.columns:
        if "descripcion" in c.lower() or "descripción" in c.lower(): col_map[c] = 'Descripción'
        if "transito" in c.lower() or "tránsito" in c.lower(): col_map[c] = 'Tránsito'
        if "vía" in c.lower() or "via" in c.lower(): col_map[c] = 'Vía'
    df = df.rename(columns=col_map)

    for index, row in df.iterrows():
        desc = str(row.get('Descripción', ''))
        transito = row.get('Tránsito', None)
        via = row.get('Vía', 'Desconocida')
        sentido = row.get('Sentido', 'N/A')
        observacion = row.get('Observación', '')
        
        # Convertir hora decimal de Excel a formato legible (HH:MM:SS)
        # Obtener la hora directamente (Pandas ya la convierte al leer el Excel)
        hora_bruta = row.get('Hora', None)
        try:
            # Intentamos formatearla a HH:MM:SS. Si ya es texto, la dejamos tal cual.
            hora_legible = pd.to_datetime(hora_bruta).strftime('%H:%M:%S')
        except:
            # Si falla (ej: es texto raro o NaN), mostramos el valor crudo para depurar
            hora_legible = str(hora_bruta) if pd.notna(hora_bruta) else "N/A"
            
        if "Tránsito con Patente Ingresada Manualmente" in desc:
            manual_pending = True
        
        try:
            val_transito = float(transito)
            is_valid_transit = pd.notna(val_transito)
        except:
            is_valid_transit = False
            
        if is_valid_transit:
            is_tag = "TAG" in desc
            
            status = "Otro"
            if manual_pending: status = "Manual (No Leído)"
            elif is_tag: status = "Leído Correctamente (TAG)"
            else: status = "Otro (Violación/Exento)"
            
            processed_rows.append({
                'Vía': via,
                'Hora': hora_legible,
                'Tránsito': int(val_transito),
                'Patente': extract_patente(observacion),
                'TAG': extract_tag(observacion),
                'Sentido': sentido,
                'Estado': status,
                'Descripción Original': desc
            })
            manual_pending = False
            
    return pd.DataFrame(processed_rows)

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