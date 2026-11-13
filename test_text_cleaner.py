
from processors.text_cleaner import (
    clean_product_name,
    normalize_material_terms
)


products = [
    "HDPE INDUSTRIAL PIPE",
    "High Density Polyethylene Sheet",
    "SS304 HEX BOLT",
    "Aluminium   6061 Rod",
    "PVC-INDUSTRIAL-SHEET",
    "AISI 316 Stainless Steel Pipe",
    "Polypropylene Plastic Sheet"
]


print("PRODUCT NAME NORMALIZATION TEST")
print("-" * 55)

for product in products:

    cleaned = clean_product_name(product)

    normalized = normalize_material_terms(product)

    print(f"Original   : {product}")
    print(f"Cleaned    : {cleaned}")
    print(f"Normalized : {normalized}")
    print("-" * 55)
