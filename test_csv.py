
from storage.csv_manager import (
    initialize_csv,
    save_raw_products,
    save_verified_products
)

initialize_csv()

sample_products = [
    {
        "product_id": "P0001",
        "product_name": "HDPE Industrial Pipe",
        "source_website": "IndiaMART",
        "source_url": "https://example.com/product1",
        "collected_date": "2026-11-12"
    }
]

save_raw_products(sample_products)

verified_products = [
    {
        "product_id": "P0001",
        "product_name": "HDPE Industrial Pipe",
        "primary_material": "Plastic",
        "material_subtype": "HDPE",
        "source_url": "https://example.com/product1",
        "verification_status": "Verified",
        "evidence_reference": "Sample verification"
    }
]

save_verified_products(verified_products)
