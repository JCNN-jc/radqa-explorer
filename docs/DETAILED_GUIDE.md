# RadQA Explorer v0.4 — Verification package

An educational Streamlit prototype for checking depth–dose CSV data, finding
the sampled peak and distal R80, comparing with a reference, and exporting
single-curve analysis and comparison results. All bundled examples are synthetic teaching/test data.
The app does not establish clinical QA results or treatment guidance.

## Start on Windows

Extract this ZIP into a new folder. Open PowerShell in the folder containing
`app.py` and run (Python 3.10 or later):

```powershell
py -m pip install -r requirements_app.txt
py -m streamlit run app.py
```

If asked for an email, leave it blank and press Enter. Open the Local URL
printed by Streamlit, usually http://localhost:8501, and keep PowerShell open.
Ctrl+C stops the app. On macOS/Linux, use `python3` instead of `py`.
If an older copy is running, stop it first and launch this new folder's app.

## Try the +2 mm demonstration

1. Upload `data/fixtures/upload_shifted_curve.csv` as the current curve.
2. Set **Reference source** to **Bundled synthetic teaching data**.
3. Check current peak = **12 mm**, current R80 = **13 mm**, reference R80 =
   **11 mm**, and **ΔR80 = +2 mm**.
4. Inspect the blue current curve and orange dashed reference curve in the
   same chart. Both use their original sampling grids and input dose values.
5. Click **Download comparison results (CSV)** and open it in Excel. Check
   current R80 13, reference R80 11, delta 2, comparison status `ok`.

To supply your own reference, select **Upload reference CSV** and use its
separate upload button. Removing a current upload restores the default
synthetic curve. Selecting **No reference** restores single-curve mode.

## CSV requirements and interpretation

Required column names are exactly `depth_mm,relative_dose_percent`.
Use UTF-8 CSV (BOM accepted), at most 5 MB per file, with at least two data rows.
Depths must be strictly increasing. Depth and dose must be finite and
non-negative. Missing cells/columns, nonnumeric values, duplicate depths, and
unordered depths produce explicit errors. Invalid current or reference inputs
stop result rendering, including the download button, so no stale analysis is
presented. Files are read into memory; the application does not save uploads
to disk. Bundled references are labeled synthetic; uploaded sources are not
verified by the app.

R80 uses 80% of each curve's own sampled maximum, taking the first descending
crossing after the first maximum and interpolating linearly within its bracket.
No extrapolation, automatic normalization, alignment, or resampling occurs.
ΔR80 is current R80 minus reference R80. Both datasets must use a common depth
origin, coordinate convention, and units. A positive difference means a greater
crossing depth for the current curve, without any clinical pass/fail judgment.
If either R80 is not evaluable, ΔR80 is also **Not evaluable**, with an explanation.

## Result downloads

The existing **Download analysis results (CSV)** button exports the current
curve only. It includes source filename/type, point count, peak, R80, status,
method, and educational-use statement. Unevaluable R80 values are blank,
with status `not_evaluable`. A separate **Download comparison results (CSV)** button appears when a valid
reference file has been loaded. It exports one comparison row, including:

- `current_...` and `reference_...`: filename, source type, point count, peak
  depth/dose, distal R80, R80 target, status, and reason for each input.
- `delta_r80_mm`: current minus reference; positive, negative, or zero.
- `comparison_status`: `ok` when both R80 values are evaluable;
  `not_evaluable` otherwise, with an explicit `comparison_explanation`.
- Difference definition, interpolation convention, coordinate assumption, and
  educational-use statement.

When either R80 is unavailable, the corresponding R80 field and delta field
are empty (never replaced by zero). A true zero difference is exported as 0.
The comparison remains downloadable so its unavailable status can be recorded.
No reference / no reference file means no comparison button. Invalid input
means no result buttons; exports are rebuilt from the current inputs on every
rerun. CSV uses UTF-8 with BOM for Excel. Filenames containing commas or quotes
are quoted by Python's CSV writer.

## Acceptance checks

| Current input | Reference | Expected result |
| --- | --- | --- |
| Default fixture | No reference | Peak 10 mm, R80 11 mm; export matches |
| `upload_shifted_curve.csv` | Bundled synthetic | Peak 12 mm, R80 13 mm; reference R80 11 mm; ΔR80 +2 mm |
| Default fixture | Uploaded shifted curve | ΔR80 −2 mm |
| Default fixture | Bundled synthetic | ΔR80 0 mm |
| `upload_no_crossing.csv` | Bundled synthetic | Current R80 and ΔR80 Not evaluable; chart retained; exported current R80 blank |
| Default fixture | Uploaded no-crossing curve | Reference R80 and ΔR80 Not evaluable; chart retained |
| `upload_invalid_missing_column.csv` | Any | Error; no metrics/chart/download |
| Valid curve | Uploaded invalid CSV | Reference error; no metrics/chart/download |
| Valid curve | Upload mode, no reference file | Current analysis available; comparison awaits a file |

Run the original calculation check:

```powershell
py src/analyze_curve.py --self-check
```

Check the CSV export cases (positive, negative, zero, either/both missing,
filename quoting, and report context):

```powershell
py -m unittest discover -s tests -v
```

For missing-current or missing-reference cases, open the downloaded comparison
CSV and check blank delta plus `not_evaluable`; the reason must identify the
curve(s) that cannot be evaluated. For invalid inputs, verify both download
buttons disappear. Also change the reference back to **No reference** and
confirm the comparison button disappears.

This package runs locally; it is not a published public website.


## Verification package (2026-10-19)

The app and calculation/export modules are unchanged from v0.4. This package
adds four input-validation tests, three additional invalid CSV fixtures, and
an English test record. All fixtures remain synthetic teaching/test data.

Run the standard tests from the folder containing `app.py`:

```powershell
py -m unittest discover -s tests -v
py src/analyze_curve.py --self-check
```

Expected: **7 test methods pass**, including four new rejection checks:
missing column, nonnumeric value, duplicate depth, and unordered depth.
The existing three comparison-export methods contain several parameterized
cases; the count of methods is not the count of individual scenarios.

See `verification/TEST_RECORD.md` for this package's observed results and test
limitations, `verification/unit_tests.txt` for raw test output, and
`verification/exports/` for actual comparison files downloaded during browser
checks. These checks were performed in the assistant's Linux environment;
Windows checks on your computer should be recorded separately.

### Optional browser automation (developer use)

These steps are not needed to run the app or the standard Python tests.
With Node.js installed, install the pinned test-only browser dependency:

```powershell
npm install --no-save --package-lock=false playwright@1.51.1
npx playwright install chromium
```

Keep the app running on localhost:8501. In a second terminal in this folder:

```powershell
node tests/browser_checks.cjs
```

The browser script checks five comparisons and each invalid fixture in both
input roles, saves the actual downloaded comparison files under
`verification/exports/`, and writes `verification/browser_results.json`.
It overwrites these evidence files on a successful rerun; keep a copy if needed.
Use `RADQA_TEST_URL` for a different app address, or
`RADQA_BROWSER_EXECUTABLE` for an existing Chromium executable.
