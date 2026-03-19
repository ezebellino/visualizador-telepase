import sys
import pathlib

import pandas as pd
import pytest

# Ensure project root is in sys.path for tests to import local modules
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
    assert extract_tag("Número: ABC987") == "ABC987"


def test_extract_tag_missing():
    assert extract_tag("No hay tag") == "N/A"
    assert extract_tag(None) == "N/A"


def test_find_header_and_data():
    data = [
        ["texto", "irrelevante", "x"],
        ["Hora", "Vía", "Descripción"],
        ["12:00", "Norte", "Tránsito con TAG"],
    ]
    df_raw = pd.DataFrame(data)
    df_result = find_header_and_data(df_raw)
    assert df_result is not None
    assert "Hora" in df_result.columns
    assert df_result.iloc[0]["Vía"] == "Norte"


def test_process_events_classification():
    rows = [
        {
            "Hora": "08:00",
            "Vía": "Norte",
            "Tránsito": 1,
            "Descripción": "TAG OK",
            "Observación": "Patente: ABC123 Tag: TAG001",
        },
        {
            "Hora": "08:10",
            "Vía": "Norte",
            "Tránsito": 2,
            "Descripción": "Tránsito con Patente Ingresada Manualmente",
            "Observación": "Patente: XYZ987",
        },
        {
            "Hora": "08:15",
            "Vía": "Norte",
            "Tránsito": 3,
            "Descripción": "Violación",
            "Observación": "",
        },
    ]
    df_input = pd.DataFrame(rows)

    df_output = process_events(df_input)
    assert len(df_output) == 3
    assert "Leído Correctamente (TAG)" in df_output["Estado"].values
    assert "Manual (No Leído)" in df_output["Estado"].values
    assert "Otro (Violación/Exento)" in df_output["Estado"].values


def test_process_events_group_priority_manual():
    rows = [
        {
            "Hora": "08:00",
            "Vía": "Norte",
            "Tránsito": 5,
            "Descripción": "TAG OK",
            "Observación": "Patente: CDE456 Tag: TAG789",
        },
        {
            "Hora": "08:01",
            "Vía": "Norte",
            "Tránsito": 5,
            "Descripción": "Tránsito con Patente Ingresada Manualmente",
            "Observación": "Patente: CDE456",
        },
    ]
    df_input = pd.DataFrame(rows)

    df_output = process_events(df_input)
    assert len(df_output) == 1
    assert df_output.loc[0, "Estado"] == "Manual (No Leído)"


def test_validate_columns_raises():
    data = [{"Hora": "08:00", "Tránsito": 1, "Descripción": "TAG OK"}]
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        process_events(df)


def test_load_data_detects_semicolon_csv():
    from io import StringIO

    csv_data = "Hora;Vía;Tránsito;Descripción\n08:00;Norte;1;TAG OK\n"
    dummy = StringIO(csv_data)
    dummy.name = "data.csv"

    df = load_data(dummy)
    assert df is not None
    assert "Hora" in df.columns
    assert df.iloc[0]["Vía"] == "Norte"


def test_process_events_inherit_transito():
    rows = [
        {
            "Hora": "08:00",
            "Vía": "Norte",
            "Tránsito": 1,
            "Descripción": "TAG OK",
            "Observación": "Patente: ABC123 Tag: TAG001",
        },
        {
            "Hora": "08:01",
            "Vía": "Norte",
            "Tránsito": None,
            "Descripción": "Tarjeta leída",
            "Observación": "",
        },
        {
            "Hora": "08:02",
            "Vía": "Norte",
            "Tránsito": 2,
            "Descripción": "Otra entrada",
            "Observación": "Patente: XYZ999",
        },
    ]
    df_input = pd.DataFrame(rows)

    df_output = process_events(df_input)
    assert len(df_output) == 2
    assert (df_output["Tránsito"] == 1).any()
    assert (df_output["Tránsito"] == 2).any()


def test_process_events_infer_sentido_from_via():
    rows = [
        {
            "Hora": "08:00",
            "Vía": "11",
            "Tránsito": 1,
            "Descripción": "TAG OK",
            "Observación": "Patente: ABC123 Tag: TAG001",
            "Sentido": "N/A",
        },
        {
            "Hora": "08:02",
            "Vía": "51",
            "Tránsito": 2,
            "Descripción": "TAG OK",
            "Observación": "Patente: XYZ999",
            "Sentido": "",
        },
    ]
    df_input = pd.DataFrame(rows)

    df_output = process_events(df_input)
    assert df_output.loc[df_output["Tránsito"] == 1, "Sentido"].iloc[0] == "Asc"
    assert df_output.loc[df_output["Tránsito"] == 2, "Sentido"].iloc[0] == "Desc"


def test_process_events_sentido_normalizado():
    rows = [
        {
            "Hora": "09:00",
            "Vía": "7",
            "Tránsito": 3,
            "Descripción": "TAG OK",
            "Observación": "",
            "Sentido": "Ascendente",
        },
        {
            "Hora": "09:02",
            "Vía": "51",
            "Tránsito": 4,
            "Descripción": "TAG OK",
            "Observación": "",
            "Sentido": "Descending",
        },
    ]
    df_input = pd.DataFrame(rows)

    df_output = process_events(df_input)
    assert df_output.loc[df_output["Tránsito"] == 3, "Sentido"].iloc[0] == "Asc"
    assert df_output.loc[df_output["Tránsito"] == 4, "Sentido"].iloc[0] == "Desc"
