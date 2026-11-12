# Windows acceptance record

Date: __________  Python version: __________  Windows version: __________

Only enter actual observations. All browser checks below are pending.

| Check | Expected | Observed | Result |
| --- | --- | --- | --- |
| Automated tests | 7 methods, OK | | Pending |
| Calculation self-check | PASS | | Pending |
| Default, no reference | Peak 10 mm, R80 11 mm; curve visible | | Pending |
| Shifted current, bundled reference | Current peak 12 mm, R80 13 mm; reference R80 11 mm; delta +2 mm | | Pending |
| No-crossing current, bundled reference | R80 and delta Not evaluable; chart retained | | Pending |
| Missing-column current | Specific error; old metrics, chart and download buttons disappear | | Pending |
| Nonnumeric current | Specific error; old outputs disappear | | Pending |
| Duplicate-depth current | Specific error; old outputs disappear | | Pending |
| Unordered-depth current | Specific error; old outputs disappear | | Pending |
| Comparison CSV, shifted current | Current R80 13, reference 11, delta 2, status ok | | Pending |
| Comparison CSV, no-crossing current | Current R80 and delta blank; status not_evaluable | | Pending |

Files are in `data/fixtures/`. Before each invalid-input check, restore a valid comparison so that clearing old outputs is observable. For invalid reference checks, repeat the four invalid files using the reference uploader.

Setup issues / exact errors: __________
