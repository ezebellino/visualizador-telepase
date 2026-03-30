import datetime
import socket

import pandas as pd

DISPLAY_COLUMNS = [
    "Hora",
    "Vía",
    "Patente",
    "TAG",
    "Forma de Pago",
    "Categoria",
    "Sentido",
    "Tránsito",
    "Estado",
    "Violacion Via Abierta",
    "Descripción Original",
]

STATUS_READ = "Leido Correctamente (TAG)"
STATUS_MANUAL = "Manual (No Leido)"
STATUS_OTHER = "Otro (Violacion/Exento)"


def prepare_processed_data(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["Hora_dt"] = pd.to_datetime(prepared["Hora"], errors="coerce", format="mixed")
    prepared["Vía"] = prepared["Vía"].astype(str).str.strip()
    prepared["Sentido"] = prepared["Sentido"].astype(str).str.strip()
    prepared["Violacion Via Abierta"] = prepared.get("Violacion Via Abierta", False)
    if not isinstance(prepared["Violacion Via Abierta"], pd.Series):
        prepared["Violacion Via Abierta"] = pd.Series(
            [prepared["Violacion Via Abierta"]] * len(prepared), index=prepared.index
        )
    prepared["Violacion Via Abierta"] = (
        prepared["Violacion Via Abierta"].fillna(False).astype(bool)
    )
    prepared["Forma de Pago"] = prepared.get("Forma de Pago", "Sin dato")
    if not isinstance(prepared["Forma de Pago"], pd.Series):
        prepared["Forma de Pago"] = pd.Series(
            [prepared["Forma de Pago"]] * len(prepared), index=prepared.index
        )
    prepared["Forma de Pago"] = prepared["Forma de Pago"].fillna("Sin dato").astype(str)
    prepared["Categoria"] = prepared.get("Categoria", "N/A")
    if not isinstance(prepared["Categoria"], pd.Series):
        prepared["Categoria"] = pd.Series(
            [prepared["Categoria"]] * len(prepared), index=prepared.index
        )
    prepared["Categoria"] = prepared["Categoria"].fillna("N/A").astype(str)
    return prepared


def resolve_time_bounds(df: pd.DataFrame) -> tuple[datetime.time, datetime.time]:
    hora_series = df["Hora_dt"]
    min_hora = hora_series.min()
    max_hora = hora_series.max()

    start = min_hora.time() if pd.notna(min_hora) else datetime.time(0, 0)
    end = max_hora.time() if pd.notna(max_hora) else datetime.time(23, 59)
    return start, end


def validate_filter_inputs(
    vias: list[str],
    sentidos: list[str],
    start_time: datetime.time,
    end_time: datetime.time,
) -> None:
    if not vias:
        raise ValueError("Debes seleccionar al menos una via para analizar.")
    if not sentidos:
        raise ValueError("Debes seleccionar al menos un sentido para analizar.")
    if start_time > end_time:
        raise ValueError("La hora de inicio no puede ser mayor que la hora de fin.")


def apply_filters(
    df: pd.DataFrame,
    vias: list[str],
    sentidos: list[str],
    patente_filter: str,
    start_time: datetime.time,
    end_time: datetime.time,
) -> pd.DataFrame:
    validate_filter_inputs(vias, sentidos, start_time, end_time)

    filtered = df[df["Vía"].isin(vias)]
    filtered = filtered[filtered["Sentido"].isin(sentidos)]

    if patente_filter:
        filtered = filtered[
            filtered["Patente"]
            .astype(str)
            .str.contains(patente_filter.strip(), case=False, na=False)
        ]

    filtered = filtered[filtered["Hora_dt"].notna()]
    filtered = filtered[
        (filtered["Hora_dt"].dt.time >= start_time)
        & (filtered["Hora_dt"].dt.time <= end_time)
    ]
    return filtered


def build_summary(df: pd.DataFrame) -> dict[str, float | int]:
    counts = df["Estado"].value_counts()
    total = len(df)
    reads = counts.get(STATUS_READ, 0)
    manuals = counts.get(STATUS_MANUAL, 0)
    others = counts.get(STATUS_OTHER, 0)
    effectiveness = (reads / total * 100) if total else 0.0
    return {
        "total": total,
        "reads": reads,
        "manuals": manuals,
        "others": others,
        "effectiveness": effectiveness,
    }


def build_operational_insights(df: pd.DataFrame) -> dict[str, str]:
    summary = build_summary(df)
    predominant_state = df["Estado"].value_counts().idxmax() if not df.empty else "N/A"
    via_count = int(df["Vía"].nunique()) if "Vía" in df.columns else 0

    if summary["effectiveness"] >= 85:
        effectiveness_note = "Nivel de lectura alto"
    elif summary["effectiveness"] >= 60:
        effectiveness_note = "Nivel de lectura intermedio"
    else:
        effectiveness_note = "Nivel de lectura bajo"

    return {
        "effectiveness_note": effectiveness_note,
        "predominant_state": predominant_state,
        "via_count": str(via_count),
    }


def build_status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    status_counts = df["Estado"].value_counts().reset_index()
    status_counts.columns = ["Estado", "Cantidad"]
    return status_counts


def build_effectiveness_trend(df: pd.DataFrame) -> pd.DataFrame:
    trend_source = df.copy()
    trend_source["Hora_agrupada"] = trend_source["Hora_dt"].dt.floor("15min")
    trend = (
        trend_source.groupby("Hora_agrupada")
        .agg(
            total=("Tránsito", "count"),
            leidos=("Estado", lambda s: (s == STATUS_READ).sum()),
        )
        .reset_index()
    )
    trend["Efectividad"] = trend["leidos"] / trend["total"] * 100
    return trend


def build_status_by_via(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    estado_via = df.groupby(["Vía", "Estado"]).size().reset_index(name="Cantidad")
    pivot = estado_via.pivot(index="Vía", columns="Estado", values="Cantidad").fillna(0)
    return estado_via, pivot


def build_direction_summary(df: pd.DataFrame) -> dict[str, int]:
    counts = df["Sentido"].value_counts()
    asc = int(counts.get("Asc", 0))
    desc = int(counts.get("Desc", 0))
    return {
        "asc": asc,
        "desc": desc,
        "saldo_pendiente": max(asc - desc, 0),
    }


def build_payment_summary(df: pd.DataFrame) -> dict[str, int]:
    counts = df["Forma de Pago"].fillna("Sin dato").value_counts()
    return {
        "tag": int(counts.get("Tag", 0)),
        "efectivo": int(counts.get("Efectivo", 0)),
        "sin_dato": int(counts.get("Sin dato", 0)),
    }


def build_payment_insights(df: pd.DataFrame) -> dict[str, float | int]:
    summary = build_payment_summary(df)
    known_total = summary["tag"] + summary["efectivo"]
    overall_total = known_total + summary["sin_dato"]

    tag_share = (summary["tag"] / known_total * 100) if known_total else 0.0
    efectivo_share = (summary["efectivo"] / known_total * 100) if known_total else 0.0
    unknown_share = (summary["sin_dato"] / overall_total * 100) if overall_total else 0.0

    return {
        "tag": summary["tag"],
        "efectivo": summary["efectivo"],
        "sin_dato": summary["sin_dato"],
        "known_total": known_total,
        "overall_total": overall_total,
        "tag_share": tag_share,
        "efectivo_share": efectivo_share,
        "unknown_share": unknown_share,
    }


def build_payment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    payment_counts = df["Forma de Pago"].fillna("Sin dato").value_counts().reset_index()
    payment_counts.columns = ["Forma de Pago", "Cantidad"]
    return payment_counts


def build_category_distribution(df: pd.DataFrame) -> pd.DataFrame:
    category_counts = df["Categoria"].fillna("N/A").astype(str).value_counts().reset_index()
    category_counts.columns = ["Categoria", "Cantidad"]
    category_counts["Categoria_orden"] = pd.to_numeric(
        category_counts["Categoria"], errors="coerce"
    )
    return category_counts.sort_values(
        by=["Categoria_orden", "Categoria"], na_position="last"
    ).drop(columns=["Categoria_orden"])


def build_open_violation_summary(df: pd.DataFrame) -> tuple[int, pd.DataFrame]:
    violations = df[df["Violacion Via Abierta"]]
    by_via = violations.groupby("Vía").size().reset_index(name="Cantidad")
    by_via = by_via.sort_values("Cantidad", ascending=False)
    return int(len(violations)), by_via


def build_network_access_urls(port: int = 8501) -> dict[str, list[str] | str]:
    local_url = f"http://127.0.0.1:{port}"
    ip_candidates: set[str] = set()

    try:
        hostname_ips = socket.gethostbyname_ex(socket.gethostname())[2]
        ip_candidates.update(ip for ip in hostname_ips if not ip.startswith("127."))
    except OSError:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip_candidates.add(sock.getsockname()[0])
    except OSError:
        pass

    network_urls = [f"http://{ip}:{port}" for ip in sorted(ip_candidates)]
    return {"local_url": local_url, "network_urls": network_urls}
