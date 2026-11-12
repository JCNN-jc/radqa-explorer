"""Known-answer checks for comparison CSV contents and missing-value handling."""
import csv
from io import StringIO
from pathlib import Path
import unittest

from src.analyze_curve import load_curve, find_peak, distal_r80
from src.comparison_export import comparison_record, csv_bytes

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def analyze(name):
    points = load_curve(FIXTURES / name)
    peak = find_peak(points)
    r80 = distal_r80(points, peak)
    return dict(input_file=name, data_type="Synthetic teaching data",
                number_of_points=len(points), peak_depth_mm=peak.depth_mm,
                peak_relative_dose_percent=peak.value,
                distal_r80_mm=r80.depth_mm if r80.depth_mm is not None else "",
                r80_status=r80.status, r80_target_relative_dose_percent=r80.target_value,
                r80_explanation=r80.message)


class ComparisonExportTest(unittest.TestCase):
    def setUp(self):
        self.base = analyze("day3_handcheck_curve.csv")
        self.shifted = analyze("upload_shifted_curve.csv")
        self.missing = analyze("upload_no_crossing.csv")

    def exported(self, current, reference):
        payload = csv_bytes(comparison_record(current, reference))
        self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
        return next(csv.DictReader(StringIO(payload.decode("utf-8-sig"))))

    def test_signed_and_zero_differences(self):
        for current, reference, expected in [
            (self.shifted, self.base, 2), (self.base, self.shifted, -2),
            (self.base, self.base, 0),
        ]:
            with self.subTest(expected=expected):
                row = self.exported(current, reference)
                self.assertEqual(float(row["delta_r80_mm"]), expected)
                self.assertEqual(row["comparison_status"], "ok")
                self.assertEqual(row["current_input_file"], current["input_file"])
                self.assertEqual(row["reference_input_file"], reference["input_file"])

    def test_either_or_both_missing(self):
        for current, reference in [(self.missing, self.base),
                                   (self.base, self.missing), (self.missing, self.missing)]:
            with self.subTest(current=current["input_file"], reference=reference["input_file"]):
                row = self.exported(current, reference)
                self.assertEqual(row["delta_r80_mm"], "")
                self.assertEqual(row["comparison_status"], "not_evaluable")
                for role, a in [("current", current), ("reference", reference)]:
                    if a["r80_status"] != "ok":
                        self.assertEqual(row[f"{role}_distal_r80_mm"], "")
                        self.assertIn(role.capitalize()+":", row["comparison_explanation"])

    def test_csv_quotes_and_context(self):
        self.shifted["input_file"] = 'sample, "shifted".csv'
        row = self.exported(self.shifted, self.base)
        self.assertEqual(row["current_input_file"], self.shifted["input_file"])
        self.assertIn("no extrapolation", row["method"])
        self.assertIn("Educational", row["purpose"])


if __name__ == "__main__":
    unittest.main()
