
from datetime import datetime
import uuid

from collectors.browser_collector import BrowserCollector

from processors.material_identifier import identify_material_with_local_fallback

from storage.csv_manager import (
    initialize_csv,
    save_raw_products,
)


def collect_product():

    keyword = input("\nEnter product keyword: ").strip()

    if not keyword:
        print("Keyword cannot be empty.")
        return

    collector = BrowserCollector()

    try:
        product = collector.get_top_product(keyword)

    except Exception as error:
        print("\nCollection failed:", error)
        return

    product_id = str(uuid.uuid4())

    product_name = product["product_name"]
    source_url = product["source_url"]

    # Save raw product
    result = identify_material_with_local_fallback(product_name)
    raw_product = {
        "product_id": product_id,
        "product_name": product_name,
        "source_website": "TradeIndia",
        "source_url": source_url,
        "collected_date": datetime.now().strftime("%Y-%m-%d"),
        "material_evidence": product.get("material_evidence", ""),
        "candidate_primary_material": result["primary_material"],
        "candidate_material_subtype": result["material_subtype"],
        "classification_status": result["status"],
        "classifier_source": result["classifier_source"],
    }

    saved = save_raw_products([raw_product])

    print("\n========== MATERIAL PREDICTION ==========")
    print("Product:", product_name)
    print("Primary Material:", result["primary_material"])
    print("Material Subtype:", result["material_subtype"])
    print("Status:", result["status"])
    print("Classifier:", result["classifier_source"])
    print("Evidence:", result["evidence"])
    print("Product URL:", source_url)
    print("=========================================")

    print("Raw record saved." if saved else "Duplicate record already exists; CSV unchanged.")


def main():

    initialize_csv()

    print("========================================")
    print(" INDUSTRIAL MATERIAL DATA COLLECTOR")
    print("========================================")

    while True:

        collect_product()

        while True:
            choice = input(
                "\nSearch another product? (y/yes/n/no): "
            ).strip().lower()

            if choice in {"y", "yes"}:
                break

            if choice in {"n", "no"}:
                print("\nCollection completed.")
                return

            print("Please enter y/yes to continue or n/no to finish.")


if __name__ == "__main__":
    main()
