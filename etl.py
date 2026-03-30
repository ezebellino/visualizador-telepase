import csv
import datetime
import re

import pandas as pd

ASCENDENTES = {7, 8, 9, 10, 11}
DESCENDENTES = {51, 52, 53, 54, 55}
SENTIDO_ASC = "Asc"
SENTIDO_DESC = "Desc"
SENTIDO_NA = "N/A"

REQUIRED_COLUMNS = ["Hora", "Via", "Transito", "Descripcion"]
COLUMN_ALIASES = {
    "hora": "Hora",
    "via": "Via",
    "vía": "Via",
    "transito": "Transito",
    "tránsito": "Transito",
    "descripcion": "Descripcion",
    "descripción": "Descripcion",
    "sentido": "Sentido",
    "observacion": "Observacion",
    "observación": "Observacion",
    "f.pago": "FPago",
    "f pago": "FPago",
    "fpago": "FPago",
    "man": "Man",
}


def parse_hora(value):
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()
    if not text:
        return pd.NaT

    formats = [
        "%H:%M:%S",
        "%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue

    return pd.to_datetime(text, errors="coerce")


def infer_sentido_from_via(via_value):
    if pd.isna(via_value):
        return SENTIDO_NA

    matched = re.search(r"(\d+)", str(via_value).strip())
    if not matched:
        return SENTIDO_NA

    via_num = int(matched.group(1))
    if via_num in ASCENDENTES:
        return SENTIDO_ASC
    if via_num in DESCENDENTES:
        return SENTIDO_DESC
    return SENTIDO_NA


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = normalized.columns.astype(str).str.strip()

    column_map = {}
    for column in normalized.columns:
        lowered = column.lower().strip()
        column_map[column] = COLUMN_ALIASES.get(lowered, column)

    return normalized.rename(columns=column_map)


def normalize_sentido(sentido_value):
    if pd.isna(sentido_value):
        return SENTIDO_NA

    text = str(sentido_value).strip().lower()
    if not text or text in {"n/a", "na", "none", "desconocido"}:
        return SENTIDO_NA
    if "asc" in text or "sube" in text or "arriba" in text:
        return SENTIDO_ASC
    if "desc" in text or "baja" in text or "abajo" in text:
        return SENTIDO_DESC
    return SENTIDO_NA


def validate_columns(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")


def find_header_and_data(df_raw: pd.DataFrame) -> pd.DataFrame | None:
    header_idx = None
    for index, row in df_raw.head(50).iterrows():
        row_text = " ".join(row.astype(str).str.lower().values)
        if "hora" in row_text and (
            "via" in row_text
            or "vía" in row_text
            or "descripcion" in row_text
            or "descripción" in row_text
        ):
            header_idx = index
            break

    if header_idx is None:
        return None

    header_pos = df_raw.index.get_loc(header_idx)
    detected = df_raw.copy()
    detected.columns = detected.loc[header_idx]
    data = detected.iloc[header_pos + 1 :].reset_index(drop=True)
    return normalize_columns(data)


def load_data(uploaded_file) -> pd.DataFrame:
    file_extension = uploaded_file.name.split(".")[-1].lower()

    df = None
    if file_extension in ["xls", "xlsx"]:
        engine = "xlrd" if file_extension == "xls" else "openpyxl"
        try:
            df = pd.read_excel(uploaded_file, header=None, engine=engine)
        except Exception as ex:
            raise ValueError(f"No se pudo leer el archivo Excel: {ex}") from ex
    else:
        uploaded_file.seek(0)
        content = uploaded_file.read()
        if isinstance(content, bytes):
            content = content.decode("latin-1", errors="ignore")
        uploaded_file.seek(0)

        separator = ","
        try:
            separator = csv.Sniffer().sniff(content[:4096]).delimiter
        except Exception:
            separator = ","

        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(
                    uploaded_file,
                    header=None,
                    encoding=encoding,
                    sep=separator,
                    engine="python",
                    on_bad_lines="warn",
                )
                break
            except Exception:
                continue

    if df is None:
        raise ValueError("No se pudo leer el archivo cargado.")

    detected = find_header_and_data(df)
    if detected is None:
        raise ValueError("No se encontró la fila de cabecera con Hora/Via/Descripcion.")

    validate_columns(detected)
    return detected


def extract_patente(observacion) -> str:
    if pd.isna(observacion):
        return "N/A"

    match = re.search(r"Patente:\s*([A-Z0-9]+)", str(observacion), re.IGNORECASE)
    return match.group(1) if match else "N/A"


def extract_tag(observacion) -> str:
    if pd.isna(observacion):
        return "N/A"

    match = re.search(r"(?:Numero|Número|Tag):\s*([A-Z0-9]+)", str(observacion), re.IGNORECASE)
    return match.group(1) if match else "N/A"


def normalize_payment_value(value) -> str:
    if pd.isna(value):
        return "Sin dato"

    text = str(value).strip().lower()
    if not text:
        return "Sin dato"
    if "tag" in text:
        return "Tag"
    if "efe" in text:
        return "Efectivo"
    return str(value).strip()


def extract_category(description, man_value) -> str:
    if pd.notna(man_value) and str(man_value).strip():
        cleaned = str(man_value).strip()
        return cleaned[:-2] if cleaned.endswith(".0") else cleaned

    match = re.search(r"categor[ií]a\s*(\d+)", str(description), re.IGNORECASE)
    return match.group(1) if match else "N/A"


def is_open_violation(description) -> bool:
    return bool(
        re.search(r"violaci[oó]n por v[ií]a abierta", str(description), re.IGNORECASE)
    )


def assign_transito_reference(df: pd.DataFrame) -> pd.Series:
    transito_num = pd.to_numeric(df["Transito"], errors="coerce")
    via_series = df["Via"].where(df["Via"].notna(), "").astype(str).str.strip()
    description_series = df["Descripcion"].where(df["Descripcion"].notna(), "").astype(str)
    observation_series = df["Observacion"].where(df["Observacion"].notna(), "").astype(str)

    payment_series = df.get("FPago", "")
    if not isinstance(payment_series, pd.Series):
        payment_series = pd.Series([payment_series] * len(df), index=df.index)
    payment_series = payment_series.where(payment_series.notna(), "")

    hora_dt = df["Hora"].apply(parse_hora)
    next_transito = transito_num.shift(-1)
    prev_transito = transito_num.ffill()
    next_known_transito = transito_num.bfill()
    next_known_via = via_series.where(transito_num.notna()).bfill()
    next_known_hora = hora_dt.where(transito_num.notna()).bfill()
    same_via_next = via_series.eq(via_series.shift(-1))
    same_via_prev = via_series.eq(via_series.shift(1))
    same_via_next_known = via_series.eq(next_known_via)
    time_to_next = (hora_dt.shift(-1) - hora_dt).abs()
    time_to_next_known = (next_known_hora - hora_dt).abs()

    manual_like = description_series.str.contains(
        "Ingresada Manualmente", case=False, na=False
    )
    tag_no_habilitado = description_series.str.contains(
        "TAG No Habilitado", case=False, na=False
    )
    vehicle_hint = observation_series.str.contains(
        r"Patente:|Tag:|Numero:|Número:", case=False, na=False
    )
    missing_payment = payment_series.astype(str).str.strip().eq("")

    should_link_to_next = (
        transito_num.isna()
        & next_transito.notna()
        & same_via_next
        & time_to_next.le(pd.Timedelta(seconds=5)).fillna(False)
        & (manual_like | (vehicle_hint & missing_payment))
    )

    transito_ref = transito_num.copy()
    transito_ref = transito_ref.where(~should_link_to_next, next_transito)

    should_link_unknown_tag_burst = (
        transito_ref.isna()
        & tag_no_habilitado
        & next_known_transito.notna()
        & same_via_next_known
        & time_to_next_known.le(pd.Timedelta(seconds=10)).fillna(False)
    )
    transito_ref = transito_ref.where(~should_link_unknown_tag_burst, next_known_transito)

    should_link_to_prev = transito_ref.isna() & prev_transito.notna() & same_via_prev
    transito_ref = transito_ref.where(~should_link_to_prev, prev_transito)
    return transito_ref


def process_events(df: pd.DataFrame) -> pd.DataFrame:
    processed = normalize_columns(df.copy())
    validate_columns(processed)

    processed["Observacion"] = processed.get("Observacion", "")
    if not isinstance(processed["Observacion"], pd.Series):
        processed["Observacion"] = pd.Series([processed["Observacion"]] * len(processed))
    processed["Observacion"] = processed["Observacion"].fillna("")

    processed["FPago"] = processed.get("FPago", "")
    if not isinstance(processed["FPago"], pd.Series):
        processed["FPago"] = pd.Series([processed["FPago"]] * len(processed))
    processed["FPago"] = processed["FPago"].fillna("")

    processed["Man"] = processed.get("Man", "N/A")
    if not isinstance(processed["Man"], pd.Series):
        processed["Man"] = pd.Series([processed["Man"]] * len(processed))

    if "Sentido" not in processed.columns:
        processed["Sentido"] = SENTIDO_NA
    else:
        processed["Sentido"] = processed["Sentido"].fillna(SENTIDO_NA)

    processed["Hora_raw"] = processed["Hora"]
    processed["Sentido"] = processed.apply(
        lambda row: (
            infer_sentido_from_via(row["Via"])
            if normalize_sentido(row["Sentido"]) == SENTIDO_NA
            else normalize_sentido(row["Sentido"])
        ),
        axis=1,
    )

    processed["Hora_dt"] = processed["Hora"].apply(parse_hora)
    processed["Hora"] = processed["Hora_dt"].dt.strftime("%H:%M:%S")
    processed["Hora"] = (
        processed["Hora"].fillna(processed["Hora_raw"].astype(str)).replace("NaT", "N/A")
    )

    processed["Transito"] = assign_transito_reference(processed)
    processed = processed[processed["Transito"].notna()].copy()
    processed["Transito"] = processed["Transito"].astype(int)

    processed["Patente"] = processed["Observacion"].apply(extract_patente)
    processed["TAG"] = processed["Observacion"].apply(extract_tag)
    processed["Forma de Pago"] = processed["FPago"].apply(normalize_payment_value)
    processed["Categoria"] = processed.apply(
        lambda row: extract_category(row["Descripcion"], row["Man"]),
        axis=1,
    )
    processed["Violacion Via Abierta"] = processed["Descripcion"].apply(is_open_violation)

    processed["es_manual"] = processed["Descripcion"].astype(str).str.contains(
        "Tránsito con Patente Ingresada Manualmente|Transito con Patente Ingresada Manualmente",
        case=False,
        na=False,
    )
    processed["es_tag"] = processed["Descripcion"].astype(str).str.contains(
        "TAG", case=False, na=False
    )

    grouped = processed.groupby("Transito", as_index=False).agg(
        Via=("Via", lambda s: s.dropna().iloc[0] if not s.dropna().empty else "Desconocida"),
        Hora=("Hora", lambda s: s.dropna().iloc[-1] if not s.dropna().empty else "N/A"),
        Patente=("Patente", lambda s: s[s != "N/A"].iloc[-1] if not s[s != "N/A"].empty else "N/A"),
        TAG=("TAG", lambda s: s[s != "N/A"].iloc[-1] if not s[s != "N/A"].empty else "N/A"),
        Forma_de_Pago=(
            "Forma de Pago",
            lambda s: (
                "Tag"
                if (s == "Tag").any()
                else "Efectivo"
                if (s == "Efectivo").any()
                else "Sin dato"
            ),
        ),
        Categoria=("Categoria", lambda s: s[s != "N/A"].iloc[-1] if not s[s != "N/A"].empty else "N/A"),
        Sentido=("Sentido", lambda s: s.dropna().iloc[-1] if not s.dropna().empty else SENTIDO_NA),
        Descripcion_Original=(
            "Descripcion",
            lambda s: " | ".join(dict.fromkeys(s.dropna().astype(str).tolist())),
        ),
        any_manual=("es_manual", "any"),
        any_tag=("es_tag", "any"),
        any_violacion_abierta=("Violacion Via Abierta", "any"),
    )

    has_tag_device = grouped["TAG"] != "N/A"
    grouped.loc[
        (grouped["Forma_de_Pago"] == "Sin dato") & has_tag_device,
        "Forma_de_Pago",
    ] = "Tag"

    def classify(row):
        if row["any_manual"]:
            return "Manual (No Leido)"
        if row["any_tag"]:
            return "Leido Correctamente (TAG)"
        return "Otro (Violacion/Exento)"

    grouped["Estado"] = grouped.apply(classify, axis=1)

    output = grouped[
        [
            "Hora",
            "Via",
            "Transito",
            "Patente",
            "TAG",
            "Forma_de_Pago",
            "Categoria",
            "Sentido",
            "Estado",
            "any_violacion_abierta",
            "Descripcion_Original",
        ]
    ].rename(
        columns={
            "Via": "Vía",
            "Transito": "Tránsito",
            "Forma_de_Pago": "Forma de Pago",
            "Categoria": "Categoria",
            "any_violacion_abierta": "Violacion Via Abierta",
            "Descripcion_Original": "Descripción Original",
        }
    )

    return output
