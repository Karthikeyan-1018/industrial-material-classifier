
import re

from processors.text_cleaner import normalize_material_terms


# Material subtype patterns
MATERIAL_RULES = {
    "Metals": {
        "Stainless Steel": [
            r"\bstainless steel\b",
        ],
        "Mild Steel": [
            r"\bmild steel\b",
        ],
        "Carbon Steel": [
            r"\bcarbon steel\b",
        ],
        "Aluminium": [
            r"\baluminium\b",
        ],
        "Brass": [
            r"\bbrass\b",
        ],
        "Copper": [
            r"\bcopper\b",
        ],
        "Cast Iron": [
            r"\bcast iron\b",
        ],
        "Alloy Steel": [
            r"\balloy steel\b",
        ],
    },

    "Plastics": {
        "HDPE": [r"\bhdpe\b"],
        "LDPE": [r"\bldpe\b"],
        "PVC": [r"\bpvc\b"],
        "CPVC": [r"\bcpvc\b"],
        "Polypropylene": [r"\bpolypropylene\b"],
        "ABS": [r"\babs\b"],
        "Nylon": [r"\bnylon\b"],
        "PTFE": [r"\bptfe\b"],
        "Polycarbonate": [r"\bpolycarbonate\b"],
        "POM": [r"\bpom\b"],
        "PET": [r"\bpet\b"],
        "UHMWPE": [r"\buhmwpe\b"],
    }
}


def identify_material(product_name):
    """
    Identify candidate primary material and subtype
    using only the product name.

    Predictions require verification before training.
    """

    normalized_name = normalize_material_terms(product_name)

    if not normalized_name:
        return {
            "primary_material": "Unknown",
            "material_subtype": "Unknown",
            "status": "Insufficient Information",
            "evidence": "",
            "classifier_source": "Rules",
        }

    matches = []

    # Find all matching material subtypes
    for primary, subtypes in MATERIAL_RULES.items():

        for subtype, patterns in subtypes.items():

            for pattern in patterns:

                if re.search(pattern, normalized_name):

                    matches.append({
                        "primary_material": primary,
                        "material_subtype": subtype,
                        "evidence": pattern
                    })

                    break

    # Remove duplicate matches
    unique_matches = {
        (m["primary_material"], m["material_subtype"]): m
        for m in matches
    }

    matches = list(unique_matches.values())

    # No material identified
    if not matches:
        return {
            "primary_material": "Unknown",
            "material_subtype": "Unknown",
            "status": "Insufficient Information",
            "evidence": "",
            "classifier_source": "Rules",
        }

    # Multiple different material families found
    primary_categories = set(
        m["primary_material"] for m in matches
    )

    if len(primary_categories) > 1:
        return {
            "primary_material": "Unknown",
            "material_subtype": "Unknown",
            "status": "Needs Review",
            "evidence": ", ".join(
                m["material_subtype"] for m in matches
            ),
            "classifier_source": "Rules",
        }

    # Multiple subtypes within the same family
    if len(matches) > 1:
        return {
            "primary_material": matches[0]["primary_material"],
            "material_subtype": "Unknown",
            "status": "Needs Review",
            "evidence": ", ".join(
                m["material_subtype"] for m in matches
            ),
            "classifier_source": "Rules",
        }

    # One candidate identified
    result = matches[0]

    return {
        "primary_material": result["primary_material"],
        "material_subtype": result["material_subtype"],
        "status": "Candidate - Verify",
        "evidence": result["evidence"],
        "classifier_source": "Rules",
    }


def identify_material_with_local_fallback(product_name):
    """Use the name rules first, then optional local Ollama for unresolved names."""
    result = identify_material(product_name)
    if result["status"] not in ("Insufficient Information", "Needs Review"):
        return result
    if not isinstance(product_name, str) or not product_name.strip():
        return result

    from processors.ollama_material_identifier import (
        OLLAMA_MODEL,
        suggest_from_product_name,
    )

    suggestion = suggest_from_product_name(product_name, MATERIAL_RULES)
    if suggestion is None:
        result["classifier_source"] = "Rules (local Ollama unavailable or no valid suggestion)"
        return result

    result.update(suggestion)
    result["status"] = "Candidate - Verify"
    result["evidence"] = "Local Ollama suggestion from product name only; verify independently."
    result["classifier_source"] = f"Ollama {OLLAMA_MODEL} (product name only)"
    return result
