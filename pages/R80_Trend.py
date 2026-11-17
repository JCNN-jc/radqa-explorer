"""Compare dated depth–dose curves against a fixed synthetic reference."""

import csv
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter, DateFormatter, date2num
import streamlit as st

from src.analyze_curve import CurveDataError, distal_r80, find_peak, load_curve, load_uploaded_curve
from src.comparison_export import csv_records_bytes

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
REFERENCE = "day3_handcheck_curve.csv"
MEASUREMENTS = (
    (date(2026, 1, 5), REFERENCE),
    (date(2026, 1, 12), "trend_shifted_1mm.csv"),
    (date(2026, 1, 19), "upload_shifted_curve.csv"),
    (date(2026, 1, 26), "upload_no_crossing.csv"),
)


def fixture_r80(filename):
    points = load_curve(FIXTURES / filename)
    return distal_r80(points, find_peak(points))


def spreadsheet_filename(filename):
    """Keep a user-supplied filename from being evaluated as a spreadsheet formula."""
    if filename.startswith(("\t", "\r", "\n")) or filename.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + filename
    return filename


def uploaded_measurements():
    files = st.file_uploader(
        "Upload depth–dose CSVs", type=["csv"], accept_multiple_files=True,
        max_upload_size=5, key="trend_uploads",
    )
    st.caption("Required columns are depth_mm and relative_dose_percent. Use UTF-8 CSVs up to 5 MB each.")
    if not files:
        st.info("Upload one or more curves and enter a measurement date for each file.")
        st.stop()

    measurements = []
    for upload in files:
        measured_on = st.date_input(
            f"Measurement date for {upload.name}", value=None,
            key=f"trend_date_{upload.file_id}",
        )
        if measured_on is None:
            continue
        try:
            points = load_uploaded_curve(upload.getvalue())
            result = distal_r80(points, find_peak(points))
            error = None
        except UnicodeDecodeError:
            result, error = None, "Export the CSV using UTF-8 encoding."
        except (CurveDataError, csv.Error) as exc:
            result, error = None, str(exc)
        measurements.append((measured_on, upload.name, result, error))

    pending = len(files) - len(measurements)
    if pending:
        st.info(f"Enter measurement dates for the remaining {pending} file(s) to include them.")
    return sorted(measurements, key=lambda measurement: measurement[0])


st.set_page_config(page_title="R80 Trend · RadQA Explorer", page_icon="📈")
st.title("R80 Trend")
st.write("Compare distal R80 across measurement dates using a fixed synthetic reference.")
st.caption("Educational use only. The reference is synthetic teaching data.")

reference = fixture_r80(REFERENCE)
if reference.depth_mm is None:
    st.error(f"The reference R80 is not evaluable. {reference.message}")
    st.stop()

st.metric("Fixed reference distal R80", f"{reference.depth_mm:g} mm")
st.caption("ΔR80 = measurement distal R80 − reference distal R80.")

source = st.radio("Measurement source", ["Built-in teaching data", "Upload CSV files"], horizontal=True)
if source == "Built-in teaching data":
    measurements = [
        (measured_on, filename, fixture_r80(filename), None)
        for measured_on, filename in MEASUREMENTS
    ]
else:
    measurements = uploaded_measurements()
    if not measurements:
        st.stop()

rows = []
export_rows = []
deltas = []
for measured_on, filename, result, error in measurements:
    depth = result.depth_mm if result is not None else None
    delta = None if depth is None else depth - reference.depth_mm
    if error is not None:
        r80_display = delta_display = "—"
        status = f"Invalid CSV. {error}"
        status_code = "invalid_csv"
        reason = error
    elif depth is None:
        r80_display = delta_display = "Not evaluable"
        status = reason = result.message
        status_code = "not_evaluable"
    else:
        r80_display = f"{depth:g}"
        delta_display = f"{delta:+g}" if delta else "0"
        status = "Evaluable"
        status_code = "ok"
        reason = result.message
    measurement_date = measured_on.isoformat()
    deltas.append(delta)
    rows.append({
        "Date": measurement_date,
        "Curve file": filename,
        "Distal R80 (mm)": r80_display,
        "ΔR80 (mm)": delta_display,
        "Status": status,
    })
    export_rows.append({
        "measurement_date": measurement_date,
        "input_file": spreadsheet_filename(filename),
        "measurement_distal_r80_mm": depth,
        "reference_distal_r80_mm": reference.depth_mm,
        "delta_r80_mm": delta,
        "status": status_code,
        "reason": reason,
    })

dates = [measured_on for measured_on, *_ in measurements]
unique_dates = list(dict.fromkeys(dates))
fig, ax = plt.subplots(figsize=(8, 3.6), layout="constrained")
has_repeated_dates = len(unique_dates) < len(dates)
# Matplotlib breaks the line at NaN and retains the tick for the missing measurement.
ax.plot(dates, [float("nan") if delta is None else delta for delta in deltas],
        color="#2563eb", marker="o", linewidth=2, linestyle="None" if has_repeated_dates else "-")
ax.axhline(0, color="#64748b", linestyle="--", linewidth=1)
ax.set(xlabel="Measurement date", ylabel="ΔR80 (mm)")
if len(unique_dates) <= 6:
    ax.set_xticks(unique_dates)
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
else:
    locator = AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))
first_day, last_day = date2num([unique_dates[0], unique_dates[-1]])
padding = max(1, (last_day - first_day) * 0.10)
ax.set_xlim(first_day - padding, last_day + padding)
ax.margins(y=0.20)
ax.grid(axis="y", alpha=0.2)
st.pyplot(fig)
plt.close(fig)
st.caption("Measurements with no evaluable R80 have no plotted point. See the table for the reason.")
if has_repeated_dates:
    st.caption("Repeated dates use unconnected markers because no within-day order is specified.")
st.table(rows)
st.download_button(
    "Download trend results (CSV)",
    data=csv_records_bytes(export_rows),
    file_name="radqa_trend_results.csv",
    mime="text/csv",
)
st.caption("The CSV includes every row in the table. Unavailable measurement and difference values are blank.")
