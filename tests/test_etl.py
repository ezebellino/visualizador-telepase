import pathlib
import sys
from io import StringIO

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from etl import (  # noqa: E402
    extract_patente,
    extract_tag,
    find_header_and_data,
    load_data,
    process_events,
)


def test_extract_patente_found():
    assert extract_patente("Patente: ABC123") == "ABC123"
    assert extract_patente("Dato Patente: XYZ999 algo") == "XYZ999"


def test_extract_patente_missing():
    assert extract_patente("Sin patente") == "N/A"
    assert extract_patente(None) == "N/A"


def test_extract_tag_found():
    assert extract_tag("Tiene Tag: 12345") == "12345"
    assert extract_tag("Numero: ABC987") == "ABC987"


def test_extract_tag_missing():
    assert extract_tag("No hay tag") == "N/A"
    assert extract_tag(None) == "N/A"


def test_find_header_and_data():
    data = [
        ["texto", "irrelevante", "x"],
        ["Hora", "Via", "Descripcion"],
        ["12:00", "Norte", "Transito con TAG"],
    ]
    df_raw = pd.DataFrame(data)
    df_result = find_header_and_data(df_raw)
    assert df_result is not None
    assert "Hora" in df_result.columns
    assert df_result.iloc[0]["Via"] == "Norte"


def test_process_events_classification():
    rows = [
        {
            "Hora": "08:00",
            "Via": "Norte",
            "Transito": 1,
            "Descripcion": "TAG OK",
            "Observacion": "Patente: ABC123 Tag: TAG001",
            "FPago": "Tag",
            "Man": 1,
        },
        {
            "Hora": "08:10",
            "Via": "Norte",
            "Transito": 2,
            "Descripcion": "Transito con Patente Ingresada Manualmente",
            "Observacion": "Patente: XYZ987 Tag: TAG999",
        },
        {
            "Hora": "08:10",
            "Via": "Norte",
            "Transito": 2,
            "Descripcion": "Transito con TAG Pospago Categoria 1",
            "Observacion": "Patente: XYZ987 Numero: TAG999",
            "FPago": "Tag",
            "Man": 1,
        },
        {
            "Hora": "08:15",
            "Via": "Norte",
            "Transito": 3,
            "Descripcion": "Violacion por Via Abierta",
            "Observacion": "",
        },
    ]
    df_output = process_events(pd.DataFrame(rows))

    assert len(df_output) == 3
    assert "Leido Correctamente (TAG)" in df_output["Estado"].values
    assert "Manual (No Leido)" in df_output["Estado"].values
    assert "Otro (Violacion/Exento)" in df_output["Estado"].values


def test_process_events_group_priority_manual():
    rows = [
        {
            "Hora": "08:00",
            "Via": "Norte",
            "Transito": 5,
            "Descripcion": "TAG OK",
            "Observacion": "Patente: CDE456 Tag: TAG789",
            "FPago": "Tag",
        },
        {
            "Hora": "08:01",
            "Via": "Norte",
            "Transito": 5,
            "Descripcion": "Transito con Patente Ingresada Manualmente",
            "Observacion": "Patente: CDE456",
        },
    ]
    df_output = process_events(pd.DataFrame(rows))
    assert len(df_output) == 1
    assert df_output.loc[0, "Estado"] == "Manual (No Leido)"


def test_validate_columns_raises():
    data = [{"Hora": "08:00", "Transito": 1, "Descripcion": "TAG OK"}]
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        process_events(pd.DataFrame(data))


def test_load_data_detects_semicolon_csv():
    csv_data = "Hora;Via;Transito;Descripcion\n08:00;Norte;1;TAG OK\n"
    dummy = StringIO(csv_data)
    dummy.name = "data.csv"

    df = load_data(dummy)
    assert "Hora" in df.columns
    assert df.iloc[0]["Via"] == "Norte"


def test_process_events_inherit_transito_from_previous_same_via():
    rows = [
        {
            "Hora": "08:00",
            "Via": "Norte",
            "Transito": 1,
            "Descripcion": "TAG OK",
            "Observacion": "Patente: ABC123 Tag: TAG001",
            "FPago": "Tag",
        },
        {
            "Hora": "08:01",
            "Via": "Norte",
            "Transito": None,
            "Descripcion": "Tarjeta leida",
            "Observacion": "",
        },
        {
            "Hora": "08:02",
            "Via": "Sur",
            "Transito": 2,
            "Descripcion": "Otra entrada",
            "Observacion": "Patente: XYZ999",
        },
    ]
    df_output = process_events(pd.DataFrame(rows))
    assert len(df_output) == 2
    assert (df_output["Tránsito"] == 1).any()
    assert (df_output["Tránsito"] == 2).any()


def test_process_events_infer_sentido_from_via():
    rows = [
        {
            "Hora": "08:00",
            "Via": "11",
            "Transito": 1,
            "Descripcion": "TAG OK",
            "Observacion": "Patente: ABC123 Tag: TAG001",
            "Sentido": "N/A",
            "FPago": "Tag",
        },
        {
            "Hora": "08:02",
            "Via": "51",
            "Transito": 2,
            "Descripcion": "TAG OK",
            "Observacion": "Patente: XYZ999",
            "Sentido": "",
            "FPago": "Tag",
        },
    ]
    df_output = process_events(pd.DataFrame(rows))
    assert df_output.loc[df_output["Tránsito"] == 1, "Sentido"].iloc[0] == "Asc"
    assert df_output.loc[df_output["Tránsito"] == 2, "Sentido"].iloc[0] == "Desc"


def test_process_events_sentido_normalizado():
    rows = [
        {
            "Hora": "09:00",
            "Via": "7",
            "Transito": 3,
            "Descripcion": "TAG OK",
            "Observacion": "",
            "Sentido": "Ascendente",
            "FPago": "Tag",
        },
        {
            "Hora": "09:02",
            "Via": "51",
            "Transito": 4,
            "Descripcion": "TAG OK",
            "Observacion": "",
            "Sentido": "Descending",
            "FPago": "Tag",
        },
    ]
    df_output = process_events(pd.DataFrame(rows))
    assert df_output.loc[df_output["Tránsito"] == 3, "Sentido"].iloc[0] == "Asc"
    assert df_output.loc[df_output["Tránsito"] == 4, "Sentido"].iloc[0] == "Desc"


def test_process_events_manual_row_links_to_next_transit_and_keeps_payment_category():
    rows = [
        {
            "Hora": "2026-03-30 00:00:40",
            "Via": "10",
            "Transito": None,
            "Descripcion": "Transito con Patente Ingresada Manualmente",
            "Sentido": "Asc.",
            "Observacion": "Patente: AE454PV Tag: SI9099453463",
        },
        {
            "Hora": "2026-03-30 00:00:40",
            "Via": "10",
            "Transito": 440075,
            "Descripcion": "Transito con TAG Pospago Categoria 1",
            "Sentido": "Asc.",
            "Observacion": "Patente: AE454PV Numero: SI9099453463 AUBASA",
            "FPago": "Tag",
            "Man": 1,
        },
    ]

    df_output = process_events(pd.DataFrame(rows))

    assert len(df_output) == 1
    assert df_output.loc[0, "Tránsito"] == 440075
    assert df_output.loc[0, "Estado"] == "Manual (No Leido)"
    assert df_output.loc[0, "Forma de Pago"] == "Tag"
    assert df_output.loc[0, "Categoria"] == "1"


def test_process_events_marks_open_violation():
    rows = [
        {
            "Hora": "00:01:46",
            "Via": "52",
            "Transito": 676499,
            "Descripcion": "Violacion por Via Abierta",
            "Sentido": "Desc.",
            "Observacion": "",
        }
    ]

    df_output = process_events(pd.DataFrame(rows))
    assert bool(df_output.loc[0, "Violacion Via Abierta"]) is True


def test_process_events_merges_unknown_tag_burst_into_next_confirmed_transit():
    rows = [
        {
            "Hora": "2026-03-30 02:02:39",
            "Via": "53",
            "Transito": None,
            "Descripcion": "TAG No Habilitado",
            "Observacion": "Numero: SI9091439617 Tag desconocido",
        },
        {
            "Hora": "2026-03-30 02:02:40",
            "Via": "53",
            "Transito": None,
            "Descripcion": "TAG No Habilitado",
            "Observacion": "Numero: SI9099669350 Tag desconocido",
        },
        {
            "Hora": "2026-03-30 02:02:47",
            "Via": "53",
            "Transito": None,
            "Descripcion": "Transito con Patente Ingresada Manualmente",
            "Sentido": "Desc.",
            "Observacion": "Patente: LTQ093 Tag: SI9093486701",
        },
        {
            "Hora": "2026-03-30 02:02:47",
            "Via": "53",
            "Transito": 245429,
            "Descripcion": "Transito con TAG Pospago Categoria 1",
            "Sentido": "Desc.",
            "Observacion": "Patente: LTQ093 Numero: SI9093486701 AUBASA",
            "FPago": "Tag",
            "Man": 1,
        },
    ]

    df_output = process_events(pd.DataFrame(rows))
    assert len(df_output) == 1
    assert df_output.loc[0, "Tránsito"] == 245429
    assert "TAG No Habilitado" in df_output.loc[0, "Descripción Original"]
