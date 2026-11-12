"""Known bad CSVs must be rejected, never repaired or silently analyzed."""
from pathlib import Path
import unittest

from src.analyze_curve import CurveDataError, load_curve

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"


class InputValidationTest(unittest.TestCase):
    def test_missing_column_is_rejected(self):
        with self.assertRaisesRegex(CurveDataError, "Missing required column.*relative_dose_percent"):
            load_curve(FIXTURES / "upload_invalid_missing_column.csv")

    def test_nonnumeric_value_is_rejected_with_row(self):
        with self.assertRaisesRegex(CurveDataError, "Row 3.*non-numeric"):
            load_curve(FIXTURES / "upload_invalid_nonnumeric.csv")

    def test_duplicate_depth_is_rejected_with_row(self):
        with self.assertRaisesRegex(CurveDataError, "Row 4 repeats depth 10 mm"):
            load_curve(FIXTURES / "upload_invalid_duplicate_depth.csv")

    def test_unordered_depth_is_rejected_without_sorting(self):
        with self.assertRaisesRegex(CurveDataError, "not increasing at row 4.*does not reorder"):
            load_curve(FIXTURES / "upload_invalid_unordered_depth.csv")


if __name__ == "__main__":
    unittest.main()
