
import os
from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = str(PROJECT_ROOT / "data" / "raw_products.csv")
FINAL_CSV = str(PROJECT_ROOT / "data" / "industrial_products.csv")


def initialize_csv():
    """Create CSV files with headers if they do not exist."""

    os.makedirs(Path(RAW_CSV).parent, exist_ok=True)

    raw_columns = [
        "product_id",
        "product_name",
        "source_website",
        "source_url",
        "collected_date",
        "material_evidence",
        "candidate_primary_material",
        "candidate_material_subtype",
        "classification_status",
        "classifier_source",
    ]

    final_columns = [
        "product_id",
        "product_name",
        "primary_material",
        "material_subtype",
        "source_url",
        "verification_status",
        "evidence_reference"
    ]

    if not os.path.exists(RAW_CSV):
        pd.DataFrame(columns=raw_columns).to_csv(RAW_CSV, index=False)

    if not os.path.exists(FINAL_CSV):
        pd.DataFrame(columns=final_columns).to_csv(FINAL_CSV, index=False)


def save_raw_products(products):
    """Save newly collected raw product records."""

    if not products:
        return False

    initialize_csv()

    existing = pd.read_csv(RAW_CSV).reindex(columns=[
        "product_id", "product_name", "source_website", "source_url",
        "collected_date", "material_evidence", "candidate_primary_material",
        "candidate_material_subtype", "classification_status", "classifier_source",
    ])
    before = len(existing)

    new_data = pd.DataFrame(products)

    new_data = new_data.drop_duplicates(
        subset=["product_name", "source_url"]
    )

    combined = pd.concat(
        [existing, new_data],
        ignore_index=True
    )

    combined = combined.drop_duplicates(
        subset=["product_name", "source_url"]
    )

    combined.to_csv(RAW_CSV, index=False)

    added = len(combined) > before
    print(f"Raw dataset updated: {len(combined)} records.")
    return added


def save_verified_products(products):
    """Save verified and approved training records."""

    if not products:
        print("No verified products to save.")
        return

    initialize_csv()

    existing = pd.read_csv(FINAL_CSV)

    new_data = pd.DataFrame(products)

    new_data = new_data[
        (new_data["verification_status"] == "Verified")
        & new_data["primary_material"].isin(["Metals", "Plastics"])
    ]

    combined = pd.concat(
        [existing, new_data],
        ignore_index=True
    )

    combined = combined.drop_duplicates(
        subset=["product_name", "source_url"]
    )

    combined.to_csv(FINAL_CSV, index=False)

    print(f"Verified dataset updated: {len(combined)} records.")
