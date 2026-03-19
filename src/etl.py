"""Compatibility wrapper for the project's canonical ETL module.

The single source of truth lives in the top-level ``etl.py`` module.
This file re-exports that API so any legacy imports from ``src.etl``
keep working while the project structure is stabilized.
"""

from etl import (
    extract_patente,
    extract_tag,
    find_header_and_data,
    load_data,
    process_events,
)

__all__ = [
    "extract_patente",
    "extract_tag",
    "find_header_and_data",
    "load_data",
    "process_events",
]
