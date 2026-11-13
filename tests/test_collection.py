import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collectors.browser_collector import (
    _material_evidence,
    _title_matches_keyword,
    _valid_product_url,
)
from processors.material_identifier import identify_material
from processors.material_identifier import identify_material_with_local_fallback
from processors.ollama_material_identifier import suggest_from_product_name
from storage import csv_manager


class CollectionUnitTests(unittest.TestCase):
    def test_material_page_text_is_retained_as_evidence(self):
        evidence = _material_evidence(
            "Product Specifications\nMaterial\tPVC, Other\nSize: 20 mm\n"
            "Company Details\nWe also sell stainless steel fittings."
        )
        self.assertEqual(evidence, "Material\tPVC, Other")

    def test_url_validation_accepts_tradeindia_product_urls_only(self):
        self.assertTrue(_valid_product_url("https://www.tradeindia.com/products/bolt-c123.html"))
        self.assertFalse(_valid_product_url("javascript:alert(1)"))
        self.assertFalse(_valid_product_url("https://example.com/products/bolt-c123.html"))
        self.assertFalse(_valid_product_url("https://www.tradeindia.com/products/"))

    def test_listing_title_must_match_keyword(self):
        self.assertTrue(_title_matches_keyword("DIN 6921 Flange Bolt", "bolt"))
        self.assertFalse(_title_matches_keyword("Featured Products", "bolt"))
        self.assertTrue(_title_matches_keyword("Blue RAL 5010 Powder Coating", "Blue RAL 5010 Powder"))
        self.assertFalse(_title_matches_keyword("Bentonite Powder", "Blue RAL 5010 Powder"))
        self.assertFalse(_title_matches_keyword("Cera-metal Putty For Powder Coating", "RAL 5010 Powder Coating"))

    def test_identifier_accepts_only_product_name(self):
        result = identify_material("PVC Water Pipe")
        self.assertEqual(result["primary_material"], "Plastics")
        self.assertEqual(result["material_subtype"], "PVC")

    def test_ollama_candidate_uses_only_name_and_validates_subtype(self):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"response": '{"primary_material":"Metals","material_subtype":"Brass"}'}

        calls = []

        def fake_post(url, **kwargs):
            calls.append((url, kwargs))
            return FakeResponse()

        from processors.material_identifier import MATERIAL_RULES
        result = suggest_from_product_name("Brass Bolt", MATERIAL_RULES, post=fake_post)
        self.assertEqual(result, {"primary_material": "Metals", "material_subtype": "Brass"})
        prompt = calls[0][1]["json"]["prompt"]
        self.assertIn("Product name: Brass Bolt", prompt)
        self.assertNotIn("Material: Brass", prompt)

    def test_ollama_fallback_is_candidate_not_verified_ground_truth(self):
        with patch("processors.ollama_material_identifier.suggest_from_product_name", return_value={
            "primary_material": "Metals", "material_subtype": "Brass"
        }):
            result = identify_material_with_local_fallback("Unusual Fastener")
        self.assertEqual(result["status"], "Candidate - Verify")
        self.assertTrue(result["classifier_source"].startswith("Ollama"))

    def test_csv_save_is_duplicate_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = str(Path(directory) / "raw.csv")
            final = str(Path(directory) / "verified.csv")
            with patch.object(csv_manager, "RAW_CSV", raw), patch.object(csv_manager, "FINAL_CSV", final):
                csv_manager.initialize_csv()
                record = {
                    "product_id": "id1", "product_name": "PVC Water Pipe",
                    "source_website": "IndiaMART", "source_url": "https://example.com/pvc",
                    "collected_date": "2026-11-12", "material_evidence": "Material: PVC",
                    "candidate_primary_material": "Plastics", "candidate_material_subtype": "PVC",
                    "classification_status": "Candidate - Verify",
                }
                self.assertTrue(csv_manager.save_raw_products([record]))
                self.assertFalse(csv_manager.save_raw_products([record]))


if __name__ == "__main__":
    unittest.main()
