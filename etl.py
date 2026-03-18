import csv
import re
from io import StringIO

import pandas as pd

REQUIRED_COLUMNS = ['Hora', 'Vía', 'Tránsito', 'Descripción']
COLUMN_ALIASES = {
    'hora': 'Hora',
    'vía': 'Vía',
    'via': 'Vía',
    'tránsito': 'Tránsito',
    'transito': 'Tránsito',
    'descripción': 'Descripción',
    'descripcion': 'Descripción',
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {}
    for col in df.columns:
        lower = col.lower().strip()
        col_map[col] = COLUMN_ALIASES.get(lower, col)
    df = df.rename(columns=col_map)
    return df


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f'Faltan columnas requeridas: {missing}')


def find_header_and_data(df_raw: pd.DataFrame) -> pd.DataFrame | None:
    header_idx = None
    for i, row in df_raw.head(50).iterrows():
        row_text = ' '.join(row.astype(str).str.lower().values)
        if 'hora' in row_text and ('vía' in row_text or 'via' in row_text or 'descripción' in row_text or 'descripcion' in row_text):
            header_idx = i
            break
    if header_idx is None:
        return None

    df_raw.columns = df_raw.iloc[header_idx]
    data = df_raw[header_idx + 1 :].reset_index(drop=True)
    data = normalize_columns(data)
    return data


def load_data(uploaded_file) -> pd.DataFrame | None:
    file_extension = uploaded_file.name.split('.')[-1].lower()

    df = None
    if file_extension in ['xls', 'xlsx']:
        engine = 'xlrd' if file_extension == 'xls' else 'openpyxl'
        try:
            df = pd.read_excel(uploaded_file, header=None, engine=engine)
        except Exception as ex:
            raise ValueError(f'No se pudo leer el archivo Excel: {ex}')
    else:
        uploaded_file.seek(0)
        content = uploaded_file.read()
        if isinstance(content, bytes):
            content = content.decode('latin-1', errors='ignore')
        uploaded_file.seek(0)

        sep = ','
        try:
            sniff = csv.Sniffer()
            dialect = sniff.sniff(content[:4096])
            sep = dialect.delimiter
        except Exception:
            sep = ','

        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(
                    uploaded_file,
                    header=None,
                    encoding=encoding,
                    sep=sep,
                    engine='python',
                    on_bad_lines='warn',
                )
                break
            except Exception:
                continue

    if df is None:
        return None

    df = find_header_and_data(df)
    if df is None:
        raise ValueError('No se encontró la fila de cabecera con Hora/Vía/Descripción.')
    validate_columns(df)
    return df


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
    df = df.copy()
    df = normalize_columns(df)
    validate_columns(df)

    df['Observación'] = df.get('Observación', '')
    if not isinstance(df['Observación'], pd.Series):
        df['Observación'] = pd.Series([df['Observación']] * len(df))
    df['Observación'] = df['Observación'].fillna('')

    if 'Sentido' not in df.columns:
        df['Sentido'] = 'N/A'
    else:
        df['Sentido'] = df['Sentido'].fillna('N/A')

    df['Hora_raw'] = df['Hora']

    df['Hora'] = pd.to_datetime(df['Hora'], errors='coerce')
    df['Hora'] = df['Hora'].dt.strftime('%H:%M:%S')
    df['Hora'] = df['Hora'].fillna(df['Hora_raw'].astype(str)).replace('NaT', 'N/A')

    df['Tránsito'] = pd.to_numeric(df['Tránsito'], errors='coerce')
    df['Tránsito'] = df['Tránsito'].ffill()
    df = df[df['Tránsito'].notna()]
    df['Tránsito'] = df['Tránsito'].astype(int)

    df['Patente'] = df['Observación'].apply(extract_patente)
    df['TAG'] = df['Observación'].apply(extract_tag)

    df['es_manual'] = df['Descripción'].astype(str).str.contains('Tránsito con Patente Ingresada Manualmente', case=False, na=False)
    df['es_tag'] = df['Descripción'].astype(str).str.contains('TAG', case=False, na=False)

    grouped = df.groupby('Tránsito', as_index=False).agg(
        Vía=('Vía', lambda s: s.dropna().iloc[0] if not s.dropna().empty else 'Desconocida'),
        Hora=('Hora', lambda s: s.dropna().iloc[0] if not s.dropna().empty else 'N/A'),
        Patente=('Patente', lambda s: s[s != 'N/A'].iloc[0] if not s[s != 'N/A'].empty else 'N/A'),
        TAG=('TAG', lambda s: s[s != 'N/A'].iloc[0] if not s[s != 'N/A'].empty else 'N/A'),
        Sentido=('Sentido', lambda s: s.dropna().iloc[0] if not s.dropna().empty else 'N/A'),
        Descripción_Original=('Descripción', lambda s: s.dropna().iloc[0] if not s.dropna().empty else ''),
        any_manual=('es_manual', 'any'),
        any_tag=('es_tag', 'any'),
    )

    def classify(row):
        if row['any_manual']:
            return 'Manual (No Leído)'
        if row['any_tag']:
            return 'Leído Correctamente (TAG)'
        return 'Otro (Violación/Exento)'

    grouped['Estado'] = grouped.apply(classify, axis=1)

    salida = grouped[['Hora', 'Vía', 'Tránsito', 'Patente', 'TAG', 'Sentido', 'Estado', 'Descripción_Original']].rename(columns={'Descripción_Original': 'Descripción Original'})

    return salida
