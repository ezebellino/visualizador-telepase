import io

import altair as alt
import pandas as pd
import streamlit as st

from app_logging import get_logger
from app_logic import (
    DISPLAY_COLUMNS,
    STATUS_READ,
    apply_filters,
    build_effectiveness_trend,
    build_operational_insights,
    build_status_by_via,
    build_status_distribution,
    build_summary,
    prepare_processed_data,
    resolve_time_bounds,
)
from etl import load_data, process_events

st.set_page_config(page_title="Monitor de Lectura Telepase", layout="wide")
logger = get_logger()

st.markdown(
    """
    <style>
        .hero-card {
            padding: 1.25rem 1.5rem;
            border: 1px solid rgba(49, 51, 63, 0.18);
            border-radius: 18px;
            background: linear-gradient(
                135deg,
                rgba(8, 78, 156, 0.10),
                rgba(16, 185, 129, 0.10)
            );
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .hero-subtitle {
            font-size: 1rem;
            color: rgba(49, 51, 63, 0.8);
        }
        .section-note {
            padding: 0.85rem 1rem;
            border-radius: 14px;
            background: rgba(8, 78, 156, 0.06);
            border: 1px solid rgba(8, 78, 156, 0.12);
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def compute_processed(uploaded_file):
    logger.info("Procesando archivo cargado: %s", uploaded_file.name)
    df_clean = load_data(uploaded_file)
    processed = process_events(df_clean)
    logger.info(
        "Archivo procesado correctamente: %s | registros=%s",
        uploaded_file.name,
        len(processed),
    )
    return processed


def render_empty_state():
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">📡 Sistema de Monitoreo Telepase</div>
            <div class="hero-subtitle">
                Análisis operativo de lecturas TAG, fallos manuales y tránsito por vía.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Carga un archivo CSV, XLS o XLSX para ver métricas, filtros, gráficos y exportaciones."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Formatos soportados", "CSV / XLS / XLSX")
    col2.metric("Resolución", "Por tránsito")
    col3.metric("Exportación", "CSV y Excel")

    with st.expander("Qué hace esta app"):
        st.write("""
            - Detecta la cabecera real del reporte aunque el archivo tenga ruido arriba.
            - Agrupa eventos por tránsito para evitar duplicados funcionales.
            - Clasifica lecturas correctas, fallos manuales y otros estados.
            - Permite filtrar por vía, sentido, patente y rango horario.
            """)


def render_processing_error(error: Exception):
    logger.exception("Fallo al procesar el archivo: %s", error)
    st.error(f"No se pudo procesar el archivo: {error}")
    with st.expander("Sugerencias para corregir el archivo"):
        st.write("""
            - Verifica que el archivo tenga columnas equivalentes a Hora, Vía, Tránsito y Descripción.
            - Si es un CSV, confirma que no esté dañado o vacío.
            - Si es un Excel exportado manualmente, intenta volver a exportarlo desde origen.
            """)


def render_header(df_filtrado: pd.DataFrame, filters: dict):
    insights = build_operational_insights(df_filtrado)
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">📡 Sistema de Monitoreo Telepase</div>
            <div class="hero-subtitle">
                Seguimiento de lecturas, fallos y estados operativos sobre el archivo cargado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="section-note">
            <strong>Contexto actual:</strong>
            {len(df_filtrado)} registros visibles |
            Vías: {", ".join(map(str, filters["vias"]))} |
            Sentidos: {", ".join(map(str, filters["sentidos"]))} |
            Cobertura: {insights["via_count"]} vías activas |
            Diagnóstico: {insights["effectiveness_note"]}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(df_processed: pd.DataFrame, uploaded_file_name: str):
    st.sidebar.header("Filtros")
    st.sidebar.caption(f"Archivo cargado: {uploaded_file_name}")

    vias_disponibles = df_processed["Vía"].dropna().unique().tolist()
    sentidos_disponibles = df_processed["Sentido"].dropna().unique().tolist()
    min_hora, max_hora = resolve_time_bounds(df_processed)

    vias_seleccionadas = st.sidebar.multiselect(
        "Selecciona la vía a monitorear",
        options=vias_disponibles,
        default=vias_disponibles,
        help="Si deseleccionas todas, no se mostrarán datos.",
    )
    sentido_seleccionado = st.sidebar.multiselect(
        "Selecciona el sentido",
        options=sentidos_disponibles,
        default=sentidos_disponibles,
    )
    patente_filter = st.sidebar.text_input("Buscar patente (parcial)", value="")

    col_time1, col_time2 = st.sidebar.columns(2)
    start_time = col_time1.time_input("Hora inicio", min_hora)
    end_time = col_time2.time_input("Hora fin", max_hora)

    grafico_tipo = st.sidebar.selectbox(
        "Tipo de gráfico de lectura",
        ["Barra por estado", "Pie de lectura", "Línea de efectividad"],
        index=0,
        help="Elige cómo visualizar la lectura de antena.",
    )

    page_size = st.sidebar.selectbox("Tamaño de página", [25, 50, 100, 200], index=1)

    return {
        "vias": vias_seleccionadas,
        "sentidos": sentido_seleccionado,
        "patente": patente_filter,
        "start_time": start_time,
        "end_time": end_time,
        "grafico_tipo": grafico_tipo,
        "page_size": page_size,
    }


def build_chart(df_filtrado: pd.DataFrame, grafico_tipo: str):
    if grafico_tipo == "Barra por estado":
        df_chart = df_filtrado.copy()
        df_chart["Hora_agrupada"] = df_chart["Hora_dt"].dt.floor("15min")
        return (
            alt.Chart(df_chart)
            .mark_bar()
            .encode(
                x=alt.X("Hora_agrupada:T", title="Hora"),
                y=alt.Y("count():Q", title="Cantidad"),
                color=alt.Color("Estado:N", legend=alt.Legend(title="Estado")),
                tooltip=["Hora_agrupada:T", "count():Q", "Estado:N"],
            )
            .properties(height=320)
        )

    if grafico_tipo == "Pie de lectura":
        status_counts = build_status_distribution(df_filtrado)
        return (
            alt.Chart(status_counts)
            .mark_arc(innerRadius=55)
            .encode(
                theta=alt.Theta(field="Cantidad", type="quantitative"),
                color=alt.Color(
                    field="Estado", type="nominal", legend=alt.Legend(title="Estado")
                ),
                tooltip=["Estado", "Cantidad"],
            )
            .properties(height=360)
        )

    trend = build_effectiveness_trend(df_filtrado)
    return (
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("Hora_agrupada:T", title="Hora"),
            y=alt.Y("Efectividad:Q", title="Efectividad (%)"),
            tooltip=[
                "Hora_agrupada:T",
                alt.Tooltip("Efectividad:Q", format=".1f"),
            ],
        )
        .properties(height=360)
    )


def render_summary(df_filtrado: pd.DataFrame, grafico_tipo: str):
    summary = build_summary(df_filtrado)
    insights = build_operational_insights(df_filtrado)
    st.markdown("### Resumen operativo")
    st.caption(
        "Vista ejecutiva para validar volumen, calidad de lectura y distribución de estados."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total vehículos", summary["total"])
    c2.metric("Lecturas OK", summary["reads"])
    c3.metric("Manual", summary["manuals"])
    c4.metric("Otros", summary["others"])
    c5.metric("Efectividad", f"{summary['effectiveness']:.1f}%")

    st.markdown(
        f"""
        <div class="section-note">
            <strong>Lectura rápida:</strong>
            {insights["effectiveness_note"]} |
            Estado predominante: {insights["predominant_state"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.altair_chart(build_chart(df_filtrado, grafico_tipo), use_container_width=True)

    estado_via, pivot = build_status_by_via(df_filtrado)
    col_left, col_right = st.columns([1, 1.2])

    with col_left:
        st.markdown("#### Estado por vía")
        st.dataframe(pivot.astype(int), width="stretch", height=260)

    with col_right:
        st.markdown("#### Heatmap por vía y estado")
        heatmap = (
            alt.Chart(estado_via)
            .mark_rect()
            .encode(
                x=alt.X("Estado:N", title="Estado"),
                y=alt.Y("Vía:N", sort="-x", title="Vía"),
                color=alt.Color(
                    "Cantidad:Q",
                    scale=alt.Scale(scheme="yellowgreenblue"),
                    title="Cantidad",
                ),
                tooltip=["Vía", "Estado", "Cantidad"],
            )
            .properties(height=320)
        )
        st.altair_chart(heatmap, use_container_width=True)


def render_detail(df_filtrado: pd.DataFrame, page_size: int):
    st.markdown("### Exportación y detalle")
    st.caption(
        "Descarga el subconjunto filtrado o revisa el detalle paginado para auditoría manual."
    )

    export_col1, export_col2 = st.columns(2)
    csv_data = df_filtrado[DISPLAY_COLUMNS].to_csv(index=False).encode("utf-8")
    export_col1.download_button(
        "⬇️ Exportar CSV",
        data=csv_data,
        file_name="telepase_filtrado.csv",
        mime="text/csv",
        use_container_width=True,
    )

    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_filtrado[DISPLAY_COLUMNS].to_excel(
                writer, index=False, sheet_name="Telepase"
            )
        export_col2.download_button(
            "⬇️ Exportar Excel",
            data=buffer.getvalue(),
            file_name="telepase_filtrado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception as error:
        st.warning(f"No se pudo generar Excel: {error}")

    num_pages = max((len(df_filtrado) - 1) // page_size + 1, 1)
    page = st.number_input("Página", min_value=1, max_value=num_pages, value=1, step=1)
    start = (page - 1) * page_size
    end = start + page_size

    st.dataframe(
        df_filtrado[DISPLAY_COLUMNS].iloc[start:end], width="stretch", height=420
    )


def main():
    uploaded_file = st.file_uploader("Cargar archivo", type=["csv", "xls", "xlsx"])

    if uploaded_file is None:
        render_empty_state()
        return

    try:
        df_processed = prepare_processed_data(compute_processed(uploaded_file))
    except Exception as error:
        render_processing_error(error)
        return

    if df_processed.empty:
        logger.warning("Archivo sin registros utilizables: %s", uploaded_file.name)
        st.warning("El archivo se pudo leer, pero no generó registros utilizables.")
        return

    filters = render_sidebar(df_processed, uploaded_file.name)

    try:
        df_filtrado = apply_filters(
            df_processed,
            filters["vias"],
            filters["sentidos"],
            filters["patente"],
            filters["start_time"],
            filters["end_time"],
        )
    except ValueError as error:
        logger.warning("Filtro inválido aplicado: %s", error)
        st.warning(str(error))
        return

    if df_filtrado.empty:
        logger.info(
            "Filtros sin resultados | archivo=%s | vias=%s | sentidos=%s",
            uploaded_file.name,
            len(filters["vias"]),
            len(filters["sentidos"]),
        )
        st.warning("No hay datos para las opciones de filtro seleccionadas.")
        return

    render_header(df_filtrado, filters)

    if STATUS_READ not in df_filtrado["Estado"].unique():
        logger.info(
            "Subconjunto sin lecturas TAG correctas | archivo=%s",
            uploaded_file.name,
        )
        st.info(
            "No hay lecturas TAG correctas en el subconjunto actual. "
            "Revisa filtros o exporta el detalle para inspección."
        )

    tab_summary, tab_detail = st.tabs(["Resumen", "Detalle"])
    with tab_summary:
        render_summary(df_filtrado, filters["grafico_tipo"])
    with tab_detail:
        render_detail(df_filtrado, filters["page_size"])


main()
