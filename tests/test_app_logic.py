import pathlib
import sys
import datetime

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_logic import (  # noqa: E402
    STATUS_MANUAL,
    STATUS_OTHER,
    STATUS_READ,
    apply_filters,
    build_effectiveness_trend,
    build_operational_insights,
    build_summary,
    prepare_processed_data,
    resolve_time_bounds,
    validate_filter_inputs,
)


def make_dataframe():
    rows = [
        {
            "Hora": "08:00:00",
            "Vía": "Norte",
            "Patente": "ABC123",
            "TAG": "TAG001",
            "Sentido": "Asc",
            "Tránsito": 1,
            "Estado": STATUS_READ,
            "Descripción Original": "TAG OK",
        },
        {
            "Hora": "08:15:00",
            "Vía": "Norte",
            "Patente": "XYZ999",
            "TAG": "N/A",
            "Sentido": "Asc",
            "Tránsito": 2,
            "Estado": STATUS_MANUAL,
            "Descripción Original": "Manual",
        },
        {
            "Hora": "09:00:00",
            "Vía": "Sur",
            "Patente": "LMN777",
            "TAG": "N/A",
            "Sentido": "Desc",
            "Tránsito": 3,
            "Estado": STATUS_OTHER,
            "Descripción Original": "Otro",
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
        vias=["Norte"],
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
            vias=["Norte", "Sur"],
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
        assert "vía" in str(error)
    else:
        raise AssertionError("Expected ValueError when no vias are selected")

    try:
        validate_filter_inputs(["Norte"], [], datetime.time(8, 0), datetime.time(9, 0))
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
