
from processors.material_identifier import identify_material


products = [
    "HDPE Industrial Pipe",
    "SS304 Hex Bolt",
    "Aluminium 6061 Rod",
    "PVC Industrial Sheet",
    "NBR Rubber Sheet",
    "PTFE Industrial Rod",
    "Brass Hex Bar",
    "Carbon Steel Plate",
    "Industrial Composite Panel 450mm",
    "Industrial Product"
]


print("\nINDUSTRIAL MATERIAL IDENTIFICATION")
print("=" * 75)

for product in products:

    result = identify_material(product)

    print(f"\nProduct Name : {product}")
    print(f"Primary      : {result['primary_material']}")
    print(f"Subtype      : {result['material_subtype']}")
    print(f"Status       : {result['status']}")
    print(f"Evidence     : {result['evidence']}")

    print("-" * 75)
