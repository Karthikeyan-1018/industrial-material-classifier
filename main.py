
from datetime import datetime
import uuid

from collectors.browser_collector import BrowserCollector

from processors.material_identifier import identify_material_with_local_fallback
from processors.pdf_product_extractor import extract_product_names_from_pdf
from processors.excel_product_extractor import extract_product_names_from_excel

from storage.csv_manager import (
    initialize_csv,
    save_raw_products,
)


def collect_product(keyword=None):

    if keyword is None:
        keyword = input("\nEnter product keyword: ").strip()

    if not keyword:
        print("Keyword cannot be empty.")
        return False

    collector = BrowserCollector()

    try:
        product = collector.get_top_product(keyword)

    except Exception as error:
        print("\nCollection failed:", error)
        message = str(error).casefold()
        if any(term in message for term in ("rate limit", "restricted", "captcha", "access denied", "429")):
            return "blocked"
        return False

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
    return True


def get_product_names_from_file(file_type):
    file_path = input(f"\nEnter {file_type.upper()} file path: ").strip().strip('"')
    if not file_path:
        print("File path cannot be empty.")
        return []

    try:
        if file_type == "pdf":
            names = extract_product_names_from_pdf(file_path)
        else:
            names = extract_product_names_from_excel(file_path)
    except Exception as error:
        print("\nCould not extract product names:", error)
        return []

    print(f"\nAutomatically extracted {len(names)} product name(s):")
    for index, name in enumerate(names, start=1):
        print(f"{index}. {name}")
    return names


def collect_product_names(names):
    for index, name in enumerate(names, start=1):
        print(f"\nProcessing product {index} of {len(names)}: {name}")
        outcome = collect_product(name)
        if outcome == "blocked":
            print("Batch stopped because the source reported an access restriction or rate limit.")
            break


def main():

    initialize_csv()

    print("========================================")
    print(" INDUSTRIAL MATERIAL DATA COLLECTOR")
    print("========================================")

    while True:
        print("\nChoose input type:")
        print("1. Enter a product keyword")
        print("2. Extract product name(s) from a PDF")
        print("3. Extract product name(s) from an Excel sheet")
        print("0. Exit")
        mode = input("Selection: ").strip().lower()

        if mode in {"0", "q", "quit", "exit"}:
            print("\nCollection completed.")
            return
        if mode in {"1", "keyword", "k"}:
            collect_product()
        elif mode in {"2", "pdf", "p"}:
            names = get_product_names_from_file("pdf")
            if names:
                collect_product_names(names)
        elif mode in {"3", "excel", "xls", "xlsx", "e"}:
            names = get_product_names_from_file("excel")
            if names:
                collect_product_names(names)
        else:
            print("Choose 1 for keyword, 2 for PDF, 3 for Excel, or 0 to exit.")
            continue

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
