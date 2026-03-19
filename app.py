import io
import datetime

import streamlit as st
import pandas as pd
import altair as alt
from etl import load_data, process_events

st.set_page_config(page_title="Monitor de Lectura Telepase", layout="wide")


# Cache para no recomputar si no cambia input
@st.cache_data
def compute_processed(uploaded_file):
    df_clean = load_data(uploaded_file)
    return process_events(df_clean)


# --- Interfaz ---
st.title("📡 Sistema de Monitoreo Telepase")

uploaded_file = st.file_uploader("Cargar archivo", type=["csv", "xls", "xlsx"])

df_processed = pd.DataFrame()
if uploaded_file is not None:
    try:
        df_processed = compute_processed(uploaded_file)
    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")

if not df_processed.empty:
    # --- FILTROS ---
    st.sidebar.header("Filtros")

    vias_disponibles = df_processed["Vía"].dropna().unique().tolist()
    vias_seleccionadas = st.sidebar.multiselect(
        "Selecciona la Vía a monitorear:",
        options=vias_disponibles,
        default=vias_disponibles,
        help="Si deseleccionas todas, no se mostrarán datos.",
    )

    sentidos_disponibles = df_processed["Sentido"].dropna().unique().tolist()
    sentido_seleccionado = st.sidebar.multiselect(
        "Selecciona el Sentido:",
        options=sentidos_disponibles,
        default=sentidos_disponibles,
    )

    patente_filter = st.sidebar.text_input("Buscar Patente (parcial)", value="")

    # Hora filtrar
    df_processed["Hora_dt"] = pd.to_datetime(df_processed["Hora"], errors="coerce")
    min_hora = (
        df_processed["Hora_dt"].min().time()
        if pd.notna(df_processed["Hora_dt"].min())
        else datetime.time(0, 0)
    )
    max_hora = (
        df_processed["Hora_dt"].max().time()
        if pd.notna(df_processed["Hora_dt"].max())
        else datetime.time(23, 59)
    )

    col_time1, col_time2 = st.sidebar.columns(2)
    start_time = col_time1.time_input("Hora inicio", min_hora)
    end_time = col_time2.time_input("Hora fin", max_hora)

    # seleccion de tipo de gráfico de eficiencia
    grafico_tipo = st.sidebar.selectbox(
        "Tipo de gráfico de lectura",
        ["Barra por estado", "Pie de lectura", "Línea de efectividad"],
        index=0,
        help="Elige cómo visualizar la lectura de antena",
    )

    # aplicando filtros
    df_filtrado = df_processed[df_processed["Vía"].isin(vias_seleccionadas)]
    df_filtrado = df_filtrado[df_filtrado["Sentido"].isin(sentido_seleccionado)]

    if patente_filter:
        df_filtrado = df_filtrado[
            df_filtrado["Patente"]
            .astype(str)
            .str.contains(patente_filter.strip(), case=False, na=False)
        ]

    if start_time and end_time:
        df_filtrado = df_filtrado[df_filtrado["Hora_dt"].notna()]
        df_filtrado = df_filtrado[
            (df_filtrado["Hora_dt"].dt.time >= start_time)
            & (df_filtrado["Hora_dt"].dt.time <= end_time)
        ]

    if df_filtrado.empty:
        st.warning("No hay datos para las opciones de filtro seleccionadas.")
    else:
        counts = df_filtrado["Estado"].value_counts()
        total = len(df_filtrado)
        reads = counts.get("Leído Correctamente (TAG)", 0)
        manuals = counts.get("Manual (No Leído)", 0)
        others = counts.get("Otro (Violación/Exento)", 0)
        effectiveness = (reads / total * 100) if total > 0 else 0

        st.divider()
        st.markdown(
            f"### 📊 Métricas: {', '.join(map(str, vias_seleccionadas))} | Sentido: {', '.join(map(str, sentido_seleccionado))}"
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Vehículos", total)
        c2.metric("Lecturas OK", reads)
        c3.metric("Fallo (Manual)", manuals)
        c4.metric("Efectividad", f"{effectiveness:.1f}%")

        st.divider()

        # Gráfico de lectura según selección del usuario
        df_chart = df_filtrado.copy()
        if grafico_tipo == "Barra por estado":
            df_chart["Hora_agrupada"] = df_chart["Hora_dt"].dt.floor("15min")
            chart = (
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

        elif grafico_tipo == "Pie de lectura":
            status_counts = df_chart["Estado"].value_counts().reset_index()
            status_counts.columns = ["Estado", "Cantidad"]
            chart = (
                alt.Chart(status_counts)
                .mark_arc(innerRadius=50)
                .encode(
                    theta=alt.Theta(field="Cantidad", type="quantitative"),
                    color=alt.Color(
                        field="Estado",
                        type="nominal",
                        legend=alt.Legend(title="Estado"),
                    ),
                    tooltip=["Estado", "Cantidad"],
                )
                .properties(height=360)
            )

        else:  # Línea de efectividad
            df_trend = df_chart.copy()
            df_trend["Hora_agrupada"] = df_trend["Hora_dt"].dt.floor("15min")
            trend = (
                df_trend.groupby("Hora_agrupada")
                .agg(
                    total=("Tránsito", "count"),
                    leidos=(
                        "Estado",
                        lambda s: (s == "Leído Correctamente (TAG)").sum(),
                    ),
                )
                .reset_index()
            )
            trend["Efectividad"] = trend["leidos"] / trend["total"] * 100
            chart = (
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

        st.altair_chart(chart, use_container_width=True)

        st.divider()

        output_cols = [
            "Hora",
            "Vía",
            "Patente",
            "TAG",
            "Sentido",
            "Tránsito",
            "Estado",
            "Descripción Original",
        ]
        st.dataframe(df_filtrado[output_cols], width="stretch", height=420)

        csv_data = df_filtrado[output_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar CSV",
            data=csv_data,
            file_name="telepase_filtrado.csv",
            mime="text/csv",
        )

        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_filtrado[output_cols].to_excel(
                    writer, index=False, sheet_name="Telepase"
                )
            st.download_button(
                "⬇️ Exportar Excel",
                data=buffer.getvalue(),
                file_name="telepase_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            st.warning(f"No se pudo generar Excel: {e}")

        # Pivot de estados por vía
        estado_via = (
            df_filtrado.groupby(["Vía", "Estado"]).size().reset_index(name="Cantidad")
        )
        pivot = estado_via.pivot(
            index="Vía", columns="Estado", values="Cantidad"
        ).fillna(0)

        st.markdown("### 📌 Estado por Vía")
        st.dataframe(pivot.astype(int), width="stretch", height=240)

        # Heatmap
        df_heat = estado_via.copy()
        heatmap = (
            alt.Chart(df_heat)
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

        # Paginación
        page_size = st.sidebar.selectbox(
            "Tamaño de página", [25, 50, 100, 200], index=1
        )
        num_pages = (len(df_filtrado) - 1) // page_size + 1
        page = st.sidebar.number_input(
            "Página", min_value=1, max_value=num_pages, value=1, step=1
        )
        start = (page - 1) * page_size
        end = start + page_size

        st.markdown(f"### 🗂️ Tabla paginada (Página {page}/{num_pages})")
        st.dataframe(
            df_filtrado[output_cols].iloc[start:end], width="stretch", height=350
        )
