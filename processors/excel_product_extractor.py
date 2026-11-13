"""Automatically extract product names from Excel workbook columns."""

import re
from pathlib import Path

import pandas as pd


HEADER_RANK = {
    "productname": 5,
    "itemname": 5,
    "producttitle": 5,
    "itemtitle": 5,
    "product": 3,
    "item": 3,
    "goodsname": 4,
}


def _normalize_header(value):
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _unique_names(values, limit=None):
    names, seen = [], set()
    for value in values:
        if value is None or pd.isna(value):
            continue
        name = re.sub(r"\s+", " ", str(value)).strip()
        if len(name) < 2 or len(name) > 200:
            continue
        if name.casefold() not in seen:
            seen.add(name.casefold())
            names.append(name)
        if limit is not None and len(names) >= limit:
            break
    return names


def extract_product_names_from_excel(workbook_path, max_names=None):
    """Find product-name columns in all sheets and return unique non-empty values."""
    path = Path(workbook_path).expanduser()
    if path.suffix.lower() not in {".xls", ".xlsx", ".xlsm"}:
        raise ValueError("Please choose an .xls, .xlsx, or .xlsm file.")
    if not path.is_file():
        raise FileNotFoundError(f"Excel file not found: {path}")

    try:
        sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
    except ImportError as exc:
        raise RuntimeError(
            "Excel support is missing. Install the workbook readers with "
            "python -m pip install -r requirements.txt."
        ) from exc

    extracted = []
    for frame in sheets.values():
        header_row = None
        ranked_columns = []
        for row_index in range(min(15, len(frame))):
            matches = []
            for col_index, value in enumerate(frame.iloc[row_index].tolist()):
                rank = HEADER_RANK.get(_normalize_header(value), 0)
                if rank:
                    matches.append((rank, col_index))
            if matches:
                header_row = row_index
                ranked_columns = matches
                break
        if header_row is None:
            continue

        # Prefer a dedicated Product Name/Item Name column over a generic Product column.
        _, name_column = max(ranked_columns)
        extracted.extend(frame.iloc[header_row + 1:, name_column].tolist())

    names = _unique_names(extracted, limit=max_names)
    if not names:
        raise ValueError(
            "No product names were found. Add a column headed Product Name, Item Name, "
            "Product Title, Item Title, Product, Item, or Goods Name."
        )
    return names
