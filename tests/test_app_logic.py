import datetime
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_logic import (  # noqa: E402
    STATUS_MANUAL,
    STATUS_OTHER,
    STATUS_READ,
    apply_filters,
    build_category_distribution,
    build_direction_summary,
    build_effectiveness_trend,
    build_network_access_urls,
    build_open_violation_summary,
    build_operational_insights,
    build_payment_insights,
    build_payment_summary,
    build_summary,
    prepare_processed_data,
    resolve_time_bounds,
    validate_filter_inputs,
)


def make_dataframe():
    rows = [
        {
            "Hora": "08:00:00",
            "Vía": "10",
            "Patente": "ABC123",
            "TAG": "TAG001",
            "Forma de Pago": "Tag",
            "Categoria": "1",
            "Sentido": "Asc",
            "Tránsito": 1,
            "Estado": STATUS_READ,
            "Violacion Via Abierta": False,
            "Descripción Original": "TAG OK",
        },
        {
            "Hora": "08:15:00",
            "Vía": "10",
            "Patente": "XYZ999",
            "TAG": "TAG999",
            "Forma de Pago": "Tag",
            "Categoria": "2",
            "Sentido": "Asc",
            "Tránsito": 2,
            "Estado": STATUS_MANUAL,
            "Violacion Via Abierta": False,
            "Descripción Original": "Manual",
        },
        {
            "Hora": "09:00:00",
            "Vía": "52",
            "Patente": "LMN777",
            "TAG": "N/A",
            "Forma de Pago": "Efectivo",
            "Categoria": "3",
            "Sentido": "Desc",
            "Tránsito": 3,
            "Estado": STATUS_OTHER,
            "Violacion Via Abierta": True,
            "Descripción Original": "Violacion",
        },
    ]
    return prepare_processed_data(pd.DataFrame(rows))


def test_prepare_processed_data_and_time_bounds():
    df = make_dataframe()
    assert "Hora_dt" in df.columns
    start, end = resolve_time_bounds(df)
    assert start == datetime.time(8, 0)
    assert end == datetime.time(9, 0)


def test_apply_filters_by_via_patente_and_time():
    df = make_dataframe()
    filtered = apply_filters(
        df,
        vias=["10"],
        sentidos=["Asc"],
        patente_filter="ABC",
        start_time=datetime.time(7, 30),
        end_time=datetime.time(8, 5),
    )
    assert len(filtered) == 1
    assert filtered.iloc[0]["Patente"] == "ABC123"


def test_apply_filters_raises_for_inverted_time_range():
    df = make_dataframe()
    try:
        apply_filters(
            df,
            vias=["10", "52"],
            sentidos=["Asc", "Desc"],
            patente_filter="",
            start_time=datetime.time(10, 0),
            end_time=datetime.time(8, 0),
        )
    except ValueError as error:
        assert "hora de inicio" in str(error)
    else:
        raise AssertionError("Expected ValueError for inverted time range")


def test_validate_filter_inputs_requires_vias_and_sentidos():
    try:
        validate_filter_inputs([], ["Asc"], datetime.time(8, 0), datetime.time(9, 0))
    except ValueError as error:
        assert "via" in str(error)
    else:
        raise AssertionError("Expected ValueError when no vias are selected")

    try:
        validate_filter_inputs(["10"], [], datetime.time(8, 0), datetime.time(9, 0))
    except ValueError as error:
        assert "sentido" in str(error)
    else:
        raise AssertionError("Expected ValueError when no sentidos are selected")


def test_build_summary_and_effectiveness_trend():
    df = make_dataframe()
    summary = build_summary(df)
    assert summary["total"] == 3
    assert summary["reads"] == 1
    assert summary["manuals"] == 1
    assert summary["others"] == 1
    assert summary["effectiveness"] == (1 / 3) * 100

    trend = build_effectiveness_trend(df)
    assert list(trend["total"]) == [1, 1, 1]
    assert list(trend["Efectividad"]) == [100.0, 0.0, 0.0]


def test_build_operational_insights():
    df = make_dataframe()
    insights = build_operational_insights(df)
    assert insights["effectiveness_note"] == "Nivel de lectura bajo"
    assert insights["predominant_state"] in {STATUS_READ, STATUS_MANUAL, STATUS_OTHER}
    assert insights["via_count"] == "2"


def test_build_direction_payment_category_and_violation_summaries():
    df = make_dataframe()

    direction = build_direction_summary(df)
    assert direction == {"asc": 2, "desc": 1, "saldo_pendiente": 1}

    payment = build_payment_summary(df)
    assert payment == {"tag": 2, "efectivo": 1, "sin_dato": 0}
    payment_insights = build_payment_insights(df)
    assert payment_insights["known_total"] == 3
    assert payment_insights["tag_share"] == (2 / 3) * 100
    assert payment_insights["efectivo_share"] == (1 / 3) * 100
    assert payment_insights["unknown_share"] == 0.0

    category_distribution = build_category_distribution(df)
    assert list(category_distribution["Categoria"]) == ["1", "2", "3"]

    total_violations, by_via = build_open_violation_summary(df)
    assert total_violations == 1
    assert by_via.iloc[0]["Vía"] == "52"


def test_build_network_access_urls():
    urls = build_network_access_urls()
    assert urls["local_url"].startswith("http://127.0.0.1:")
    assert isinstance(urls["network_urls"], list)


def test_prepare_processed_data_normalizes_via_type_for_filters():
    df = pd.DataFrame(
        [
            {
                "Hora": "08:00:00",
                "Vía": 10,
                "Patente": "AAA111",
                "TAG": "TAG001",
                "Forma de Pago": "Tag",
                "Categoria": 1,
                "Sentido": "Asc",
                "Tránsito": 1,
                "Estado": STATUS_READ,
                "Violacion Via Abierta": False,
                "Descripción Original": "TAG OK",
            }
        ]
    )
    prepared = prepare_processed_data(df)
    filtered = apply_filters(
        prepared,
        vias=["10"],
        sentidos=["Asc"],
        patente_filter="",
        start_time=datetime.time(0, 0),
        end_time=datetime.time(23, 59),
    )
    assert len(filtered) == 1
