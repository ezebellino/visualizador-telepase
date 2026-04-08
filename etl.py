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
        lowered = str(column).strip().lower()
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
        normalized_cells = [
            str(value).strip().lower()
            for value in row.tolist()
            if pd.notna(value) and str(value).strip()
        ]
        row_text = " ".join(normalized_cells)
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


def normalize_exempt_group(group_value) -> str:
    text = "" if pd.isna(group_value) else str(group_value).strip()
    upper_text = text.upper()
    if not upper_text:
        return "Sin agrupar"
    if "AUTORIZA SUPERVISOR" in upper_text:
        return "Autoriza Supervisor"
    if "DISCAP" in upper_text:
        return "Discapacitado"
    if "POLIC" in upper_text:
        return "Policia"
    if "AMBUL" in upper_text:
        return "Ambulancia"
    if "EX COMBAT" in upper_text or "VETERANO" in upper_text:
        return "Ex Combatientes"
    if "BOMBER" in upper_text:
        return "Bomberos"
    if "PERSONAL" in upper_text:
        return "Personal propio"
    if "VIALIDAD" in upper_text:
        return "Vialidad Provincial"
    return text


def build_group_classification(group_name: str, normalized: str, upper_text: str) -> dict[str, str]:
    patente_match = re.search(r"\b([A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d{3})\b", upper_text)
    document_match = re.search(r"\b\d{6,12}\b", upper_text)
    has_real_patente = bool(patente_match and patente_match.group(1) != "SINPATE")

    if group_name in {"Policia", "Ambulancia", "Bomberos", "Vialidad Provincial"}:
        subtype = "Patente identificada" if has_real_patente else "Sin patente"
    elif group_name == "Discapacitado":
        subtype = "DNI identificado" if document_match else "Sin DNI"
    elif group_name == "Ex Combatientes":
        subtype = (
            "Veterano Malvinas"
            if "MALVINAS" in upper_text
            else "Veterano"
            if "VETERANO" in upper_text
            else "Sin detalle"
        )
    elif group_name == "Personal propio":
        if "SUTPA" in upper_text or "SINDIC" in upper_text:
            subtype = "SUTPA"
        elif "AUBASA" in upper_text:
            subtype = "AUBASA"
        else:
            subtype = "Otro"
    else:
        subtype = group_name

    return {
        "tipo": group_name,
        "subtipo": subtype,
        "detalle": normalized,
        "patente": patente_match.group(1) if patente_match else "N/A",
        "documento": document_match.group(0) if document_match else "N/A",
        "tag_ref": "N/A",
    }


def infer_group_from_supervisor_text(supervisor_text: str) -> str | None:
    police_markers = ["POLIC", "COMISAR", "DEFENSA CIVIL"]
    personal_markers = ["AUBASA", "AUMAR", "SUTPA", "SINDIC"]

    if any(marker in supervisor_text for marker in police_markers):
        return "Policia"
    if any(marker in supervisor_text for marker in personal_markers):
        return "Personal propio"
    return None


def classify_ungrouped_observation(normalized: str, upper_text: str) -> dict[str, str]:
    patente_match = re.search(r"\b([A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d{3})\b", upper_text)
    document_match = re.search(r"\b\d{6,12}\b", upper_text)
    tag_match = re.search(r"\b(SI\d+|[A-Z]{2,}\d{5,})\b", upper_text)

    inferred_group = infer_group_from_supervisor_text(upper_text)
    if inferred_group:
        return build_group_classification(inferred_group, normalized, upper_text)

    if "DISCAP" in upper_text:
        return build_group_classification("Discapacitado", normalized, upper_text)
    if "AMBUL" in upper_text:
        return build_group_classification("Ambulancia", normalized, upper_text)
    if "BOMBER" in upper_text:
        return build_group_classification("Bomberos", normalized, upper_text)
    if "EX COMBAT" in upper_text or "VETERANO" in upper_text:
        return build_group_classification("Ex Combatientes", normalized, upper_text)

    if "VIOLACIÓN POR VÍA ABIERTA" in upper_text or "VIOLACION POR VIA ABIERTA" in upper_text:
        return {
            "tipo": "Violacion operativa",
            "subtipo": "Via abierta",
            "detalle": normalized,
            "patente": patente_match.group(1) if patente_match else "N/A",
            "documento": document_match.group(0) if document_match else "N/A",
            "tag_ref": tag_match.group(1) if tag_match else "N/A",
        }
    if "VIOLACIÓN POR VÍA CERRADA" in upper_text or "VIOLACION POR VIA CERRADA" in upper_text:
        return {
            "tipo": "Violacion operativa",
            "subtipo": "Via cerrada",
            "detalle": normalized,
            "patente": patente_match.group(1) if patente_match else "N/A",
            "documento": document_match.group(0) if document_match else "N/A",
            "tag_ref": tag_match.group(1) if tag_match else "N/A",
        }

    anomaly_markers = [
        "HUELLA",
        "TRAILER",
        "VIOLACION EN TREN",
        "SALIDA ANÓMALA",
        "SALIDA ANOMALA",
        "AVANCE Y RETROCESO",
        "OPERACIÓN ABORTADA",
        "OPERACION ABORTADA",
        "RETABULACIÓN",
        "RETABULACION",
    ]
    if any(marker in upper_text for marker in anomaly_markers):
        return {
            "tipo": "Anomalia operativa",
            "subtipo": "Huella / maniobra",
            "detalle": normalized,
            "patente": patente_match.group(1) if patente_match else "N/A",
            "documento": document_match.group(0) if document_match else "N/A",
            "tag_ref": tag_match.group(1) if tag_match else "N/A",
        }

    if "TRÁNSITO EFECTIVO" in upper_text or "TRANSITO EFECTIVO" in upper_text:
        return {
            "tipo": "Cobro efectivo",
            "subtipo": "Sin novedad asociada",
            "detalle": normalized,
            "patente": patente_match.group(1) if patente_match else "N/A",
            "documento": document_match.group(0) if document_match else "N/A",
            "tag_ref": tag_match.group(1) if tag_match else "N/A",
        }

    if "TRÁNSITO PATENTE EXENTO" in upper_text or "TRANSITO PATENTE EXENTO" in upper_text:
        return {
            "tipo": "Exento identificado",
            "subtipo": "Patente exenta",
            "detalle": normalized,
            "patente": patente_match.group(1) if patente_match else "N/A",
            "documento": document_match.group(0) if document_match else "N/A",
            "tag_ref": tag_match.group(1) if tag_match else "N/A",
        }

    if "TRÁNSITO EXENTO" in upper_text or "TRANSITO EXENTO" in upper_text:
        return {
            "tipo": "Exento identificado",
            "subtipo": "Exento sin agrupacion base",
            "detalle": normalized,
            "patente": patente_match.group(1) if patente_match else "N/A",
            "documento": document_match.group(0) if document_match else "N/A",
            "tag_ref": tag_match.group(1) if tag_match else "N/A",
        }

    return {
        "tipo": "Sin agrupar",
        "subtipo": "Sin agrupar",
        "detalle": normalized,
        "patente": patente_match.group(1) if patente_match else "N/A",
        "documento": document_match.group(0) if document_match else "N/A",
        "tag_ref": tag_match.group(1) if tag_match else "N/A",
    }


def classify_exempt_observation(observation, group_value=None, description=None) -> dict[str, str]:
    text = "" if pd.isna(observation) else str(observation).strip()
    description_text = "" if pd.isna(description) else str(description).strip()
    group_name = normalize_exempt_group(group_value)
    combined_text = " | ".join(part for part in [text, description_text] if part and part != "N/A")

    if not text and not description_text:
        return {
            "tipo": group_name,
            "subtipo": "Sin clasificar",
            "detalle": "Observacion vacia",
            "patente": "N/A",
            "documento": "N/A",
            "tag_ref": "N/A",
        }

    normalized = re.sub(r"\s+", " ", combined_text or text or description_text).strip()
    upper_text = normalized.upper()
    supervisor_text = upper_text.split("OBS.SUPERVISOR:")[-1].strip()
    supervisor_core_text = supervisor_text.split("|")[0].strip()

    if group_name == "Sin agrupar":
        return classify_ungrouped_observation(normalized, upper_text)

    if group_name != "Autoriza Supervisor":
        return build_group_classification(group_name, normalized, upper_text)

    debit_match = re.search(
        r"^(?P<via>\d+)\s+(?P<patente>[A-Z0-9]{5,8})\b", supervisor_core_text
    )
    if debit_match:
        patente = debit_match.group("patente").upper()
        return {
            "tipo": group_name,
            "subtipo": "Pago con Debito",
            "detalle": f"Pago con tarjeta de debito | Patente {patente}",
            "patente": patente,
            "documento": "N/A",
            "tag_ref": "N/A",
        }

    supervisor_match = re.search(
        r"(?P<patente>[A-Z0-9]{5,8})\s+SI\d+\s+(?P<tag>[A-Z0-9]+)\s+H(?:\s+(TAG|EXENTO))?\b",
        supervisor_core_text,
    )
    if supervisor_match:
        patente = supervisor_match.group("patente").upper()
        tag_ref = supervisor_match.group("tag")
        return {
            "tipo": group_name,
            "subtipo": "TAG habilitado por Supervisor",
            "detalle": (
                "Telepase habilitado por supervisor | "
                f"Patente {patente} | Dispositivo {tag_ref}"
            ),
            "patente": patente,
            "documento": "N/A",
            "tag_ref": tag_ref,
        }

    if "REGRESA A CARGAR COMBUSTIBLE" in supervisor_text:
        ticket_match = re.search(r"TICKET\s*N[°º]?\s*(?P<ticket>\d+)", supervisor_text)
        return {
            "tipo": group_name,
            "subtipo": "Retorno justificado",
            "detalle": "Regreso autorizado para cargar combustible",
            "patente": "N/A",
            "documento": ticket_match.group("ticket") if ticket_match else "N/A",
            "tag_ref": "N/A",
        }

    inferred_group = infer_group_from_supervisor_text(supervisor_text)
    if inferred_group:
        return build_group_classification(inferred_group, normalized, upper_text)

    patente_match = re.search(r"\b([A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d{3})\b", upper_text)
    tag_match = re.search(r"\b(SI\d+|[A-Z]{2,}\d{5,})\b", upper_text)
    document_match = re.search(r"\b\d{6,12}\b", upper_text)
    return {
        "tipo": group_name,
        "subtipo": "Supervisor - Otro",
        "detalle": normalized,
        "patente": patente_match.group(1) if patente_match else "N/A",
        "documento": document_match.group(0) if document_match else "N/A",
        "tag_ref": tag_match.group(1) if tag_match else "N/A",
    }


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

    processed["Agrupacion"] = processed.get("Agrupación", processed.get("Agrupacion", "Sin agrupar"))
    if not isinstance(processed["Agrupacion"], pd.Series):
        processed["Agrupacion"] = pd.Series([processed["Agrupacion"]] * len(processed))
    processed["Agrupacion"] = processed["Agrupacion"].fillna("Sin agrupar")

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
        Observacion_Original=(
            "Observacion",
            lambda s: " | ".join(
                dict.fromkeys(
                    value for value in s.dropna().astype(str).tolist() if value.strip()
                )
            )
            or "N/A",
        ),
        Agrupacion_Original=(
            "Agrupacion",
            lambda s: normalize_exempt_group(s.dropna().astype(str).iloc[-1]) if not s.dropna().empty else "Sin agrupar",
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
    exempt_fields = grouped.apply(
        lambda row: classify_exempt_observation(
            row["Observacion_Original"],
            row["Agrupacion_Original"],
            row["Descripcion_Original"],
        ),
        axis=1,
    )
    grouped["Exento Tipo"] = exempt_fields.apply(lambda item: item["tipo"])
    grouped["Exento Subtipo"] = exempt_fields.apply(lambda item: item["subtipo"])
    grouped["Exento Detalle"] = exempt_fields.apply(lambda item: item["detalle"])
    grouped["Exento Patente"] = exempt_fields.apply(lambda item: item["patente"])
    grouped["Exento Documento"] = exempt_fields.apply(lambda item: item["documento"])
    grouped["Exento TAG"] = exempt_fields.apply(lambda item: item["tag_ref"])

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

    output["Observacion Original"] = grouped["Observacion_Original"].values
    output["Agrupacion Original"] = grouped["Agrupacion_Original"].values
    output["Exento Tipo"] = grouped["Exento Tipo"].values
    output["Exento Subtipo"] = grouped["Exento Subtipo"].values
    output["Exento Detalle"] = grouped["Exento Detalle"].values
    output["Exento Patente"] = grouped["Exento Patente"].values
    output["Exento Documento"] = grouped["Exento Documento"].values
    output["Exento TAG"] = grouped["Exento TAG"].values
    return output
