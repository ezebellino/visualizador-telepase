import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Monitor de Lectura Telepase", layout="wide")

def find_header_and_data(df_raw):
    """
    Busca la fila que contiene los encabezados reales (Hora, Vía, Descripción)
    dentro de un DataFrame crudo y devuelve el DataFrame limpio.
    """
    header_idx = None
    
    # Iteramos las primeras 50 filas buscando palabras clave
    for i, row in df_raw.head(50).iterrows():
        row_str = row.astype(str).str.lower().values
        # Buscamos 'hora' Y ('vía' o 'via' o 'descripcion') para confirmar
        # Usamos join para buscar en toda la fila de una vez
        row_text = " ".join(row_str)
        
        if "hora" in row_text and ("vía" in row_text or "via" in row_text or "descripción" in row_text):
            header_idx = i
            break
            
    if header_idx is None:
        return None
        
    # Establecemos la fila encontrada como cabecera
    df_raw.columns = df_raw.iloc[header_idx]
    
    # Tomamos los datos desde la siguiente fila en adelante
    df_clean = df_raw[header_idx + 1:].reset_index(drop=True)
    
    return df_clean

def load_data(uploaded_file):
    """
    Carga el archivo detectando si es Excel o CSV y gestionando la codificación.
    """
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df = None
    
    try:
        if file_extension in ['xls', 'xlsx']:
            # Es un Excel (Binario)
            # engine='xlrd' es necesario para .xls antiguos
            # engine='openpyxl' para .xlsx nuevos
            engine = 'xlrd' if file_extension == 'xls' else 'openpyxl'
            try:
                df = pd.read_excel(uploaded_file, header=None, engine=engine)
            except Exception as e:
                # Si falla xlrd, intentamos openpyxl por defecto o viceversa
                df = pd.read_excel(uploaded_file, header=None)
                
        else:
            # Es un CSV o Texto
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    # Leemos todo como string primero para evitar errores de columnas
                    df = pd.read_csv(uploaded_file, header=None, encoding=encoding, sep=None, engine='python')
                    break
                except Exception:
                    continue
                    
        if df is None:
            st.error("No se pudo leer el archivo. Asegúrate de que no esté corrupto.")
            return None

        # Una vez cargado 'en bruto', buscamos dónde empiezan los datos
        df_clean = find_header_and_data(df)
        
        if df_clean is None:
            st.error("Se leyó el archivo pero no se encontró la cabecera 'Hora'/'Vía'.")
            return None
            
        return df_clean

    except Exception as e:
        st.error(f"Error crítico al cargar: {str(e)}")
        return None

def process_events(df):
    processed_rows = []
    manual_pending = False
    
    # Limpieza de nombres de columnas (espacios extra)
    df.columns = df.columns.astype(str).str.strip()
    
    if 'Descripción' not in df.columns or 'Tránsito' not in df.columns:
        # Intento de recuperación si los nombres varían ligeramente
        col_map = {c: c for c in df.columns}
        for c in df.columns:
            if "descripcion" in c.lower() or "descripción" in c.lower():
                col_map[c] = 'Descripción'
            if "transito" in c.lower() or "tránsito" in c.lower():
                col_map[c] = 'Tránsito'
        df = df.rename(columns=col_map)
    
    if 'Descripción' not in df.columns or 'Tránsito' not in df.columns:
         st.error(f"Columnas no encontradas. Disponibles: {list(df.columns)}")
         return pd.DataFrame()

    for index, row in df.iterrows():
        desc = str(row['Descripción'])
        transito = row['Tránsito']
        
        if "Tránsito con Patente Ingresada Manualmente" in desc:
            manual_pending = True
        
        # Verificamos si es un número de tránsito válido (no NaN y no vacío)
        try:
            val_transito = float(transito)
            is_valid_transit = pd.notna(val_transito)
        except:
            is_valid_transit = False
            
        if is_valid_transit:
            is_tag = "TAG" in desc
            
            status = "Otro"
            if manual_pending:
                status = "Manual (No Leído)"
            elif is_tag:
                status = "Leído Correctamente (TAG)"
            else:
                status = "Otro (Violación/Exento)"
            
            processed_rows.append({
                'Tránsito': int(val_transito),
                'Estado': status,
                'Descripción Original': desc
            })
            manual_pending = False
            
    return pd.DataFrame(processed_rows)

# --- Interfaz ---
st.title("📡 Visualizador de Rendimiento de Antena Telepase")
st.markdown("Sube tu archivo `.xls` (Excel) o `.csv`. El sistema se adaptará automáticamente.")

uploaded_file = st.file_uploader("Cargar archivo", type=['csv', 'xls', 'xlsx'])

if uploaded_file is not None:
    df_clean = load_data(uploaded_file)
    
    if df_clean is not None:
        df_processed = process_events(df_clean)
        
        if not df_processed.empty:
            counts = df_processed['Estado'].value_counts()
            total = len(df_processed)
            reads = counts.get("Leído Correctamente (TAG)", 0)
            manuals = counts.get("Manual (No Leído)", 0)
            effectiveness = (reads / total * 100) if total > 0 else 0
            
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Vehículos", total)
            c2.metric("Lecturas OK", reads)
            c3.metric("Fallo (Manual)", manuals)
            c4.metric("Efectividad", f"{effectiveness:.1f}%")
            st.divider()
            
            col_chart, col_data = st.columns([1, 2])
            
            with col_chart:
                chart_data = pd.DataFrame({'Estado': counts.index, 'Cantidad': counts.values})
                base = alt.Chart(chart_data).encode(theta=alt.Theta("Cantidad", stack=True))
                pie = base.mark_arc(innerRadius=60).encode(
                    color=alt.Color("Estado", scale=alt.Scale(scheme='set1')),
                    order=alt.Order("Cantidad", sort="descending"),
                    tooltip=["Estado", "Cantidad"]
                )
                st.altair_chart(pie, theme="streamlit")
                
            with col_data:
                st.dataframe(df_processed, width='stretch', height=400)