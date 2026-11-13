"""Extract selectable product-name candidates from text-based PDF files."""

import re
from pathlib import Path

from pypdf import PdfReader


PRODUCT_LABEL_RE = re.compile(
    r"^\s*(?:product\s*name|product\s*title|item\s*name|product|item)\s*[:#\-]\s*(.*?)\s*$",
    re.IGNORECASE,
)
STANDALONE_LABEL_RE = re.compile(
    r"^\s*(?:product\s*name|product\s*title|item\s*name)\s*:?\s*$",
    re.IGNORECASE,
)
SKIP_LINE_RE = re.compile(
    r"^(?:description|specifications?|features?|quantity|price|rate|amount|"
    r"product\s*details|technical\s*data|terms\s*(?:and|&)\s*conditions)\b",
    re.IGNORECASE,
)
PRODUCT_NOUNS = {
    "pipe", "pipes", "tube", "tubes", "bolt", "bolts", "screw", "screws",
    "flange", "flanges", "sheet", "sheets", "plate", "plates", "rod", "rods",
    "bar", "bars", "valve", "valves", "pump", "pumps", "fitting", "fittings",
    "powder", "coating", "fastener", "fasteners", "film", "pellet", "pellets",
    "resin", "granule", "granules", "wire", "cable", "gasket", "gaskets",
    "nut", "nuts", "panel", "panels", "profile", "profiles", "connector",
    "connectors", "container", "containers", "sheeting", "mesh", "bearing",
    "bearings", "nozzle", "nozzles", "housing", "housings", "component",
    "components", "product", "products",
}


def _read_text(pdf_path):
    path = Path(pdf_path).expanduser()
    if path.suffix.lower() != ".pdf":
        raise ValueError("Please choose a .pdf file.")
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ValueError("This PDF is password-protected. Provide an unlocked PDF.")
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not full_text.strip():
        raise ValueError(
            "No selectable text was found in this PDF. It may be scanned; OCR is not enabled."
        )
    return full_text


def _labelled_names(lines):
    names = []
    for index, line in enumerate(lines):
        match = PRODUCT_LABEL_RE.match(line)
        if match and match.group(1):
            names.append(match.group(1).strip(" \t:;,-"))
        elif STANDALONE_LABEL_RE.match(line):
            if index + 1 < len(lines):
                names.append(lines[index + 1].strip(" \t:;,-"))
    return names


def _deduplicate(names, limit=25):
    unique, seen = [], set()
    for name in names:
        name = re.sub(r"\s+", " ", name).strip(" \t:;,-")
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            unique.append(name)
        if len(unique) >= limit:
            break
    return unique


def extract_product_names_from_pdf(pdf_path, max_names=10):
    """Automatically extract explicit product names or likely title lines.

    Only returned names are sent to the collector/classifier. PDF descriptions and
    specifications remain local and are not used as classification features.
    """
    full_text = _read_text(pdf_path)
    lines = [re.sub(r"\s+", " ", line).strip() for line in full_text.splitlines()]
    lines = [line for line in lines if line]

    labelled = _deduplicate(_labelled_names(lines), limit=max_names)
    if labelled:
        return labelled

    titles = []
    for line in lines:
        if len(line) < 3 or len(line) > 100 or SKIP_LINE_RE.match(line):
            continue
        if re.match(r"^(?:material|grade|size|colour|color|model|specification)\s*[:\t]", line, re.I):
            continue
        words = set(re.findall(r"[a-z]+", line.casefold()))
        if words & PRODUCT_NOUNS:
            titles.append(line)
    return _deduplicate(titles, limit=max_names)


def extract_product_name_candidates(pdf_path, max_candidates=25):
    """Return product-name candidates and extracted text from a selectable-text PDF.

    Text is used only to locate candidate names. The caller passes the chosen name,
    by itself, to the web collector and material classifier.
    """
    full_text = _read_text(pdf_path)
    lines = [re.sub(r"\s+", " ", line).strip() for line in full_text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise ValueError(
            "No selectable text was found in this PDF. It may be scanned; OCR is not enabled."
        )

    candidates = _labelled_names(lines)

    # If there is no explicit product-name label, offer plausible short text lines
    # for user review instead of guessing from descriptions or specifications.
    if not candidates:
        for line in lines:
            if len(line) < 3 or len(line) > 120 or SKIP_LINE_RE.match(line):
                continue
            if not re.search(r"[A-Za-z]", line):
                continue
            candidates.append(line)

    return _deduplicate(candidates, limit=max_candidates), full_text
