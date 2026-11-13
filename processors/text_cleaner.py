
import re


# Material aliases and their canonical text forms
MATERIAL_ALIASES = {
    # Metals
    "stainless steel 304": "stainless steel 304",
    "stainless steel 316": "stainless steel 316",
    "ss304": "stainless steel 304",
    "ss 304": "stainless steel 304",
    "aisi 304": "stainless steel 304",
    "ss316": "stainless steel 316",
    "ss 316": "stainless steel 316",
    "aisi 316": "stainless steel 316",
    "mild steel": "mild steel",
    "ms": "mild steel",
    "aluminium": "aluminium",
    "aluminum": "aluminium",

    # Plastics
    "high density polyethylene": "hdpe",
    "hdpe": "hdpe",
    "low density polyethylene": "ldpe",
    "ldpe": "ldpe",
    "polyvinyl chloride": "pvc",
    "pvc": "pvc",
    "chlorinated polyvinyl chloride": "cpvc",
    "cpvc": "cpvc",
    "polypropylene": "polypropylene",
    "pp": "polypropylene",
    "acrylonitrile butadiene styrene": "abs",
    "abs": "abs",
    "polytetrafluoroethylene": "ptfe",
    "ptfe": "ptfe",
    "polycarbonate": "polycarbonate",
    "nylon": "nylon",
    "polyoxymethylene": "pom",
}


def clean_product_name(product_name):
    """
    Basic text cleaning:
    - Convert to lowercase
    - Remove extra spaces
    - Replace unnecessary punctuation
    """

    if not isinstance(product_name, str):
        return ""

    text = product_name.lower().strip()

    # Replace hyphens and underscores with spaces
    text = re.sub(r"[-_]", " ", text)

    # Keep letters, numbers and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_material_terms(product_name):
    """
    Normalize common material names and abbreviations.
    """

    text = clean_product_name(product_name)

    # Process longer aliases first
    aliases = sorted(
        MATERIAL_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for alias, canonical in aliases:

        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"

        text = re.sub(
            pattern,
            canonical,
            text
        )

    # Remove extra spaces after replacement
    text = re.sub(r"\s+", " ", text)

    return text.strip()
