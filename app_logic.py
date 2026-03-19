import datetime

import pandas as pd

DISPLAY_COLUMNS = [
    "Hora",
    "Vía",
    "Patente",
    "TAG",
    "Sentido",
    "Tránsito",
    "Estado",
    "Descripción Original",
]

STATUS_READ = "Leído Correctamente (TAG)"
STATUS_MANUAL = "Manual (No Leído)"
STATUS_OTHER = "Otro (Violación/Exento)"


def prepare_processed_data(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["Hora_dt"] = pd.to_datetime(
        prepared["Hora"], errors="coerce", format="mixed"
    )
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
        raise ValueError("Debes seleccionar al menos una vía para analizar.")
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
