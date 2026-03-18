import os
import sys
import pathlib

import pandas as pd
import pytest

# Ensure project root is in sys.path for tests to import local modules
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from etl import extract_patente, extract_tag, find_header_and_data, process_events


def test_extract_patente_found():
    assert extract_patente('Patente: ABC123') == 'ABC123'
    assert extract_patente('Dato Patente: XYZ999 algo') == 'XYZ999'


def test_extract_patente_missing():
    assert extract_patente('Sin patente') == 'N/A'
    assert extract_patente(None) == 'N/A'


def test_extract_tag_found():
    assert extract_tag('Tiene Tag: 12345') == '12345'
    assert extract_tag('Número: ABC987') == 'ABC987'


def test_extract_tag_missing():
    assert extract_tag('No hay tag') == 'N/A'
    assert extract_tag(None) == 'N/A'


def test_find_header_and_data():
    data = [
        ['texto', 'irrelevante', 'x'],
        ['Hora', 'Vía', 'Descripción'],
        ['12:00', 'Norte', 'Tránsito con TAG'],
    ]
    df_raw = pd.DataFrame(data)
    df_result = find_header_and_data(df_raw)
    assert df_result is not None
    assert 'Hora' in df_result.columns
    assert df_result.iloc[0]['Vía'] == 'Norte'


def test_process_events_classification():
    rows = [
        {'Hora': '08:00', 'Vía': 'Norte', 'Tránsito': 1, 'Descripción': 'TAG OK', 'Observación': 'Patente: ABC123 Tag: TAG001'},
        {'Hora': '08:10', 'Vía': 'Norte', 'Tránsito': 2, 'Descripción': 'Tránsito con Patente Ingresada Manualmente', 'Observación': 'Patente: XYZ987'},
        {'Hora': '08:15', 'Vía': 'Norte', 'Tránsito': 3, 'Descripción': 'Violación', 'Observación': ''},
    ]
    df_input = pd.DataFrame(rows)

    df_output = process_events(df_input)
    assert len(df_output) == 3
    assert 'Leído Correctamente (TAG)' in df_output['Estado'].values
    assert 'Manual (No Leído)' in df_output['Estado'].values
    assert 'Otro (Violación/Exento)' in df_output['Estado'].values
