from __future__ import annotations

import io
import time as time_module
from datetime import datetime, time

import pandas as pd
from fastapi import UploadFile

from app_logic import (
    apply_filters,
    build_category_distribution,
    build_effectiveness_trend,
    build_exempt_analysis,
    build_operational_insights,
    build_payment_distribution,
    build_status_by_via,
    build_status_distribution,
    build_summary,
    prepare_processed_data,
)
from etl import load_data, process_events

from .observability import configure_logging, log_event
from .schemas import (
    DashboardRecord,
    DashboardResponse,
    DistributionItem,
    ExemptRecord,
    FilterOptions,
    MetricCard,
    TrendPoint,
    ViaStatusItem,
)

logger = configure_logging()

DISPLAY_COLUMN_MAP = {
    0: "hora",
    1: "via",
    2: "transito",
    3: "patente",
    4: "tag",
    5: "forma_pago",
    6: "categoria",
    7: "sentido",
    8: "estado",
    9: "violacion_via_abierta",
    10: "descripcion_original",
}


def _parse_time(raw_value: str | None, fallback: time) -> time:
    if not raw_value:
        return fallback
    return time.fromisoformat(raw_value)


async def _load_processed_dataframe(uploaded_file: UploadFile) -> pd.DataFrame:
    file_name = uploaded_file.filename or "telepase-report.csv"
    content = await uploaded_file.read()
    file_size_bytes = len(content)
    buffer = io.BytesIO(content)
    buffer.name = file_name
    cleaned = load_data(buffer)
    return prepare_processed_data(process_events(cleaned)), file_size_bytes


def _serialize_distribution(
    frame: pd.DataFrame, label_column: str, value_column: str
) -> list[DistributionItem]:
    if frame.empty:
        return []

    return [
        DistributionItem(label=str(row[label_column]), value=int(row[value_column]))
        for _, row in frame.iterrows()
    ]


def _serialize_trend(frame: pd.DataFrame) -> list[TrendPoint]:
    if frame.empty:
        return []

    return [
        TrendPoint(
            time=row["Hora_agrupada"].isoformat() if pd.notna(row["Hora_agrupada"]) else "",
            effectiveness=round(float(row["Efectividad"]), 2),
        )
        for _, row in frame.iterrows()
    ]


def _serialize_status_by_via(frame: pd.DataFrame) -> list[ViaStatusItem]:
    if frame.empty:
        return []

    return [
        ViaStatusItem(
            via=str(row[frame.columns[0]]),
            estado=str(row["Estado"]),
            cantidad=int(row["Cantidad"]),
        )
        for _, row in frame.iterrows()
    ]


def _serialize_records(frame: pd.DataFrame) -> list[DashboardRecord]:
    selected = frame.iloc[:, :11].copy()
    selected.columns = [DISPLAY_COLUMN_MAP[index] for index in range(11)]
    return [
        DashboardRecord(
            hora=str(row["hora"]),
            via=str(row["via"]),
            patente=str(row["patente"]),
            tag=str(row["tag"]),
            forma_pago=str(row["forma_pago"]),
            categoria=str(row["categoria"]),
            sentido=str(row["sentido"]),
            transito=int(row["transito"]),
            estado=str(row["estado"]),
            violacion_via_abierta=bool(row["violacion_via_abierta"]),
            descripcion_original=str(row["descripcion_original"]),
        )
        for row in selected.to_dict(orient="records")
    ]


def _serialize_exempt_records(frame: pd.DataFrame) -> list[ExemptRecord]:
    if frame.empty:
        return []

    return [
        ExemptRecord(
            hora=str(row["Hora"]),
            via=str(row[frame.columns[1]]),
            patente=str(row["Patente"]),
            agrupacion=str(row["Agrupacion"]),
            tipo=str(row["Tipo"]),
            subtipo=str(row["Subtipo"]),
            detalle=str(row["Detalle"]),
            documento=str(row["Documento"]),
            tag_ref=str(row["TAG Ref"]),
            observacion=str(row["Observacion"]),
        )
        for row in frame.to_dict(orient="records")
    ]


async def build_dashboard_response(
    request_id: str,
    uploaded_file: UploadFile,
    vias: list[str] | None = None,
    sentidos: list[str] | None = None,
    patente: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> DashboardResponse:
    started_at = time_module.perf_counter()
    file_name = uploaded_file.filename or "telepase-report.csv"
    try:
        processed, file_size_bytes = await _load_processed_dataframe(uploaded_file)
    except Exception as exc:
        log_event(
            logger,
            "dashboard_build_failed",
            request_id=request_id,
            file_name=file_name,
            selected_vias=vias or [],
            selected_sentidos=sentidos or [],
            patente=patente or "",
            start_time=start_time or "",
            end_time=end_time or "",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise

    via_column = processed.columns[1]
    available_vias = sorted(processed[via_column].dropna().astype(str).unique().tolist())
    available_sentidos = (
        sorted(processed["Sentido"].dropna().astype(str).unique().tolist())
    )

    min_hora = processed["Hora_dt"].min()
    max_hora = processed["Hora_dt"].max()
    fallback_start = min_hora.time() if pd.notna(min_hora) else time(0, 0)
    fallback_end = max_hora.time() if pd.notna(max_hora) else time(23, 59)

    filtered = apply_filters(
        processed,
        vias or available_vias,
        sentidos or available_sentidos,
        patente or "",
        _parse_time(start_time, fallback_start),
        _parse_time(end_time, fallback_end),
    )

    summary = build_summary(filtered)
    insights = build_operational_insights(filtered)
    status_by_via, _ = build_status_by_via(filtered)
    exempt_analysis = build_exempt_analysis(filtered)

    metrics = [
        MetricCard(label="Transitos visibles", value=summary["total"]),
        MetricCard(
            label="Base real antena",
            value=summary["antenna_base"],
            delta=f"Efectivo excluido: {summary['cash_excluded']}",
        ),
        MetricCard(
            label="Lecturas correctas",
            value=summary["antenna_reads"],
            delta=f"{round(summary['antenna_read_rate'], 1)}% sobre base antena",
        ),
        MetricCard(
            label="Ingresadas manual",
            value=summary["antenna_manuals"],
            delta=f"{round(summary['antenna_manual_rate'], 1)}% sobre base antena",
        ),
        MetricCard(
            label="Efectividad real antena",
            value=round(summary["antenna_read_rate"], 1),
            delta=insights["effectiveness_note"],
        ),
    ]

    highlights = [
        f"{insights['predominant_state']} es el estado dominante del lote analizado.",
        f"{insights['via_count']} vias activas quedaron incluidas en el tablero actual.",
        "La API reutiliza el ETL actual para sostener consistencia funcional durante la migracion.",
    ]

    duration_ms = round((time_module.perf_counter() - started_at) * 1000, 2)
    status_distribution = build_status_distribution(filtered)
    payment_distribution = build_payment_distribution(filtered)
    category_distribution = build_category_distribution(filtered)
    effectiveness_trend = build_effectiveness_trend(filtered)

    log_event(
        logger,
        "dashboard_built",
        request_id=request_id,
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        total_transits=int(summary["total"]),
        antenna_base=int(summary["antenna_base"]),
        antenna_reads=int(summary["antenna_reads"]),
        antenna_manuals=int(summary["antenna_manuals"]),
        antenna_read_rate=round(float(summary["antenna_read_rate"]), 2),
        exempt_total=int(exempt_analysis["total"]),
        exempt_classified=int(exempt_analysis["classified"]),
        predominant_state=insights["predominant_state"],
        active_vias=int(insights["via_count"]),
        selected_vias=vias or available_vias,
        selected_sentidos=sentidos or available_sentidos,
        patente=patente or "",
        start_time=start_time or "",
        end_time=end_time or "",
        duration_ms=duration_ms,
    )

    return DashboardResponse(
        generated_at=datetime.utcnow().isoformat(),
        file_name=file_name,
        total_records=len(filtered),
        filters=FilterOptions(vias=available_vias, sentidos=available_sentidos),
        headline="Centro de monitoreo Telepase",
        highlights=highlights,
        metrics=metrics,
        status_distribution=_serialize_distribution(status_distribution, "Estado", "Cantidad"),
        payment_distribution=_serialize_distribution(payment_distribution, "Forma de Pago", "Cantidad"),
        category_distribution=_serialize_distribution(category_distribution, "Categoria", "Cantidad"),
        effectiveness_trend=_serialize_trend(effectiveness_trend),
        status_by_via=_serialize_status_by_via(status_by_via),
        records=_serialize_records(filtered),
        exempt_total=int(exempt_analysis["total"]),
        exempt_supervisor_total=int(exempt_analysis["supervisor_total"]),
        exempt_classified=int(exempt_analysis["classified"]),
        exempt_distribution=_serialize_distribution(
            exempt_analysis["distribution"], "Tipo", "Cantidad"
        ),
        exempt_supervisor_distribution=_serialize_distribution(
            exempt_analysis["supervisor_distribution"], "Tipo", "Cantidad"
        ),
        exempt_records=_serialize_exempt_records(exempt_analysis["records"]),
    )
