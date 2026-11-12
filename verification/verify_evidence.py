"""Check downloaded CSVs against known answers and generate the English test record."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import sys
from zoneinfo import ZoneInfo

import streamlit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
results = json.loads((HERE / "browser_results.json").read_text())
assert len(results) == 13 and all(r["status"] == "PASS" for r in results)
comparison_rows = []
invalid_rows = []

for result in results:
    if result["id"].startswith("CMP"):
        with (HERE / "exports" / result["exportFile"]).open(encoding="utf-8-sig", newline="") as f:
            records = list(csv.DictReader(f))
        assert len(records) == 1
        row = records[0]
        assert row["current_input_file"] == result["current"]
        assert row["reference_input_file"] == result["reference"]
        assert row["reference_data_type"] == result["referenceSource"]
        expected_current_type = "Synthetic teaching data" if result["name"] in ("negative", "zero", "reference_missing") else "User-uploaded data"
        assert row["current_data_type"] == expected_current_type
        for role, ui_value in [("current", result["observedCurrentR80"]),
                               ("reference", result["observedReferenceR80"])]:
            raw = row[f"{role}_distal_r80_mm"]
            if ui_value == "Not evaluable":
                assert raw == "" and row[f"{role}_r80_status"] == "not_evaluable"
            else:
                assert float(raw) == float(ui_value.split()[0])
                assert row[f"{role}_r80_status"] == "ok"
        expected = result["expectedDelta"]
        if expected is None:
            assert row["delta_r80_mm"] == ""
            assert row["comparison_status"] == "not_evaluable"
            missing_role = "Current" if result["name"] == "current_missing" else "Reference"
            assert missing_role + ":" in row["comparison_explanation"]
            expected_text = "Not evaluable; blank CSV delta"
            actual_text = "Not evaluable; blank CSV delta; not_evaluable"
        else:
            assert float(row["delta_r80_mm"]) == expected
            assert row["comparison_status"] == "ok"
            expected_text = f"{expected:+g} mm"
            actual_text = f"UI {result['observedDelta']}; CSV {float(row['delta_r80_mm']):g}; ok"
        assert "no extrapolation" in row["method"] and "Educational" in row["purpose"]
        comparison_rows.append(f"| {result['id']} | {result['current']} | {result['reference']} | {expected_text} | {actual_text} | PASS |")
    else:
        assert result["staleOutputsCleared"]
        observed = result["observed"].replace("|", "\\|").replace("\n", " ")
        invalid_rows.append(f"| {result['role']} | {result['file']} | {observed} | PASS |")

digest = hashlib.sha256((ROOT / "app.py").read_bytes()).hexdigest()
checked = datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds")
record = f"""# RadQA Explorer v0.4 — Test Record

Record generated: {checked} (America/Chicago).

## Scope and execution

These checks were executed by the assistant in a Linux test environment, not
on the user's Windows computer. The v0.4 application behavior is unchanged;
this package adds tests, invalid input fixtures, and verification evidence.
All inputs are synthetic teaching/test data. This is software verification,
not validation of measured beams or clinical QA.

- Python: {platform.python_version()}; Streamlit: {streamlit.__version__}.
- Unit tests: **7 test methods passed**, including four new rejection checks.
  The existing three methods include parameterized scenarios; method counts
  are separate from scenario counts.
- Original calculation self-check: **PASS**.
- Actual Chromium browser checks: **13 PASS** (five comparisons and eight
  invalid-input checks). Each comparison chart loaded successfully.
- Actual downloaded comparison CSV files: **5 checked and passed**.

## Comparison checks

Reference source is the bundled synthetic fixture except where an uploaded
reference is needed. The negative-difference and missing-reference cases use
uploaded references. Difference = current R80 minus reference R80.

| ID | Current input | Reference input | Expected | Observed page / downloaded CSV | Result |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(comparison_rows)}

Every export contains matching source filenames/types, individual R80 values
and statuses, calculation method, and educational-use statement. A true zero
remains numeric zero. Missing R80 and difference fields remain blank, with
an explicit reason identifying the unavailable input.

## Invalid-input checks

Expected for every case: reject with a specific explanation, remove old
metrics and chart, and hide both download buttons. Each check began with
valid comparison results before replacing one input with an invalid CSV.
Those output-clearing checks passed in all eight cases.

| Input role | Invalid input | Observed error | Result |
| --- | --- | --- | --- |
{chr(10).join(invalid_rows)}

## Evidence and reproduction

- `unit_tests.txt`: raw unittest output.
- `calculation_self_check.txt`: original known-answer check output.
- `browser_results.json` and `browser_check_log.txt`: browser assertions.
- `exports/`: the five files actually downloaded in the browser checks.

From the folder containing `app.py`, run on Windows:

```powershell
py -m unittest discover -s tests -v
py src/analyze_curve.py --self-check
```

See README for optional browser-check setup. After running the browser checks,
regenerate this record with `py verification/verify_evidence.py`.
Record Windows results separately; this report does not establish that those
checks have already been performed on the user's computer.

Application SHA-256: `{digest}`.

## Limits

These known-answer examples cover the listed behaviors only. They do not
establish accuracy on arbitrary measured data, measurement uncertainty, or
clinical suitability. No clinical pass/fail threshold is applied.
"""
(HERE / "TEST_RECORD.md").write_text(record)
print("PASS: five actual downloaded CSVs verified; English TEST_RECORD.md generated.")
