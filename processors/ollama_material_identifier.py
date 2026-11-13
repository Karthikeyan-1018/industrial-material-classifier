"""Optional local Ollama fallback for names the rules cannot classify."""

import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def suggest_from_product_name(product_name, material_rules, post=requests.post):
    """Ask a local model for an unverified candidate using only product_name."""
    if not isinstance(product_name, str) or not product_name.strip():
        return None

    allowed = {
        family: list(subtypes.keys())
        for family, subtypes in material_rules.items()
    }
    system = (
        "Suggest the most likely material classification for an industrial product, "
        "using the product name as the only input. You may use general learned knowledge "
        "to make a best-effort inference from the name. Choose the most likely family and "
        "subtype from the allowed pairs even if the name omits an explicit material, when "
        "a reasonable candidate exists. Use Unknown only when no sensible candidate can "
        "be inferred. Return a JSON object with exactly primary_material and "
        "material_subtype. This is an unverified suggestion and must never be treated as "
        "ground truth."
    )
    prompt = (
        f"Allowed family/subtype pairs: {json.dumps(allowed)}\n"
        f"Product name: {product_name.strip()}"
    )
    try:
        response = post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": system,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0},
            },
            # First inference may need to load the 8B model into memory.
            timeout=(2, 120),
        )
        response.raise_for_status()
        payload = response.json()
        result = json.loads(payload.get("response", "{}"))
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return None

    if not isinstance(result, dict):
        return None
    family = result.get("primary_material")
    subtype = result.get("material_subtype")
    if not isinstance(family, str) or not isinstance(subtype, str):
        return None
    family = family.strip().title()
    family = {"Metal": "Metals", "Plastic": "Plastics"}.get(family, family)
    subtype = subtype.strip()
    canonical_subtypes = {
        name.casefold(): (material, name)
        for material, subtypes in material_rules.items()
        for name in subtypes
    }
    canonical = canonical_subtypes.get(subtype.casefold())
    if canonical is None or canonical[0] != family:
        return None
    return {
        "primary_material": family,
        "material_subtype": canonical[1],
    }
