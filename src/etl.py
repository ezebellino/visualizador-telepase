import re
import pandas as pd


def find_header_and_data(df_raw: pd.DataFrame) -> pd.DataFrame | None:
    header_idx = None
    for i, row in df_raw.head(50).iterrows():
        row_text = " ".join(row.astype(str).str.lower().values)
        if "hora" in row_text and ("vía" in row_text or "via" in row_text or "descripción" in row_text):
            header_idx = i
            break
    if header_idx is None:
        return None
    df_raw.columns = df_raw.iloc[header_idx]
    return df_raw[header_idx + 1 :].reset_index(drop=True)


def load_data(uploaded_file) -> pd.DataFrame | None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df = None

    if file_extension in ['xls', 'xlsx']:
        engine = 'xlrd' if file_extension == 'xls' else 'openpyxl'
        try:
            df = pd.read_excel(uploaded_file, header=None, engine=engine)
        except Exception:
            df = pd.read_excel(uploaded_file, header=None)
    else:
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, header=None, encoding=encoding, sep=None, engine='python')
                break
            except Exception:
                continue

    if df is None:
        return None
    return find_header_and_data(df)


def extract_patente(obs) -> str:
    if pd.isna(obs):
        return 'N/A'
    match = re.search(r'Patente:\s*([A-Z0-9]+)', str(obs), re.IGNORECASE)
    return match.group(1) if match else 'N/A'


def extract_tag(obs) -> str:
    if pd.isna(obs):
        return 'N/A'
    match = re.search(r'(?:Número|Tag):\s*([A-Z0-9]+)', str(obs), re.IGNORECASE)
    return match.group(1) if match else 'N/A'


def process_events(df: pd.DataFrame) -> pd.DataFrame:
    processed_rows = []
    manual_pending = False

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    col_map = {c: c for c in df.columns}
    for c in df.columns:
        if 'descripcion' in c.lower() or 'descripción' in c.lower():
            col_map[c] = 'Descripción'
        if 'transito' in c.lower() or 'tránsito' in c.lower():
            col_map[c] = 'Tránsito'
        if 'vía' in c.lower() or 'via' in c.lower():
            col_map[c] = 'Vía'
    df = df.rename(columns=col_map)

    for _, row in df.iterrows():
        desc = str(row.get('Descripción', ''))
        transito = row.get('Tránsito', None)
        via = row.get('Vía', 'Desconocida')
        sentido = row.get('Sentido', 'N/A')
        observacion = row.get('Observación', '')

        hora_bruta = row.get('Hora', None)
        try:
            hora_legible = pd.to_datetime(hora_bruta).strftime('%H:%M:%S')
        except Exception:
            hora_legible = str(hora_bruta) if pd.notna(hora_bruta) else 'N/A'

        if 'Tránsito con Patente Ingresada Manualmente' in desc:
            manual_pending = True

        try:
            val_transito = float(transito)
            is_valid_transit = pd.notna(val_transito)
        except Exception:
            is_valid_transit = False

        if is_valid_transit:
            is_tag = 'TAG' in desc
            status = 'Otro'
            if manual_pending:
                status = 'Manual (No Leído)'
            elif is_tag:
                status = 'Leído Correctamente (TAG)'
            else:
                status = 'Otro (Violación/Exento)'

            processed_rows.append({
                'Vía': via,
                'Hora': hora_legible,
                'Tránsito': int(val_transito),
                'Patente': extract_patente(observacion),
                'TAG': extract_tag(observacion),
                'Sentido': sentido,
                'Estado': status,
                'Descripción Original': desc,
            })
            manual_pending = False

    return pd.DataFrame(processed_rows)
