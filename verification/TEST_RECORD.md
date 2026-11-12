# RadQA Explorer v0.4 — Test Record

Record generated: 2026-10-26T20:53:52-05:00 (America/Chicago).

## Scope and execution

These checks were executed by the assistant in a Linux test environment, not
on the user's Windows computer. The v0.4 application behavior is unchanged;
this package adds tests, invalid input fixtures, and verification evidence.
All inputs are synthetic teaching/test data. This is software verification,
not validation of measured beams or clinical QA.

- Python: 3.12.14; Streamlit: 1.65.0.
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
| CMP01 | upload_shifted_curve.csv | day3_handcheck_curve.csv | +2 mm | UI +2 mm; CSV 2; ok | PASS |
| CMP02 | day3_handcheck_curve.csv | upload_shifted_curve.csv | -2 mm | UI -2 mm; CSV -2; ok | PASS |
| CMP03 | day3_handcheck_curve.csv | day3_handcheck_curve.csv | +0 mm | UI +0 mm; CSV 0; ok | PASS |
| CMP04 | upload_no_crossing.csv | day3_handcheck_curve.csv | Not evaluable; blank CSV delta | Not evaluable; blank CSV delta; not_evaluable | PASS |
| CMP05 | day3_handcheck_curve.csv | upload_no_crossing.csv | Not evaluable; blank CSV delta | Not evaluable; blank CSV delta; not_evaluable | PASS |

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
| current | upload_invalid_missing_column.csv | Cannot analyze current CSV: Missing required column(s): relative_dose_percent. Expected: depth_mm and relative_dose_percent. | PASS |
| current | upload_invalid_nonnumeric.csv | Cannot analyze current CSV: Row 3 has a non-numeric depth or dose value. | PASS |
| current | upload_invalid_duplicate_depth.csv | Cannot analyze current CSV: Row 4 repeats depth 10 mm. Resolve duplicates explicitly. | PASS |
| current | upload_invalid_unordered_depth.csv | Cannot analyze current CSV: Depths are not increasing at row 4 (8 mm follows 10 mm). The script does not reorder input data. | PASS |
| reference | upload_invalid_missing_column.csv | Cannot analyze reference CSV: Missing required column(s): relative_dose_percent. Expected: depth_mm and relative_dose_percent. | PASS |
| reference | upload_invalid_nonnumeric.csv | Cannot analyze reference CSV: Row 3 has a non-numeric depth or dose value. | PASS |
| reference | upload_invalid_duplicate_depth.csv | Cannot analyze reference CSV: Row 4 repeats depth 10 mm. Resolve duplicates explicitly. | PASS |
| reference | upload_invalid_unordered_depth.csv | Cannot analyze reference CSV: Depths are not increasing at row 4 (8 mm follows 10 mm). The script does not reorder input data. | PASS |

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

Application SHA-256: `5cdfebbb4e418f5cd1d4a87272e42a4a866191ab162abbe37051b6db1180cb7a`.

## Limits

These known-answer examples cover the listed behaviors only. They do not
establish accuracy on arbitrary measured data, measurement uncertainty, or
clinical suitability. No clinical pass/fail threshold is applied.
