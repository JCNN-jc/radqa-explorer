"""RadQA Explorer v0.4: educational comparison and CSV reporting."""
import csv
from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from src.analyze_curve import CurveDataError, distal_r80, find_peak, load_curve, load_curve_stream
from src.comparison_export import comparison_record, csv_bytes

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "data" / "fixtures" / "day3_handcheck_curve.csv"


def read_points(upload):
    """Use one validator for both inputs; uploads stay in memory."""
    if upload is None:
        points = load_curve(FIXTURE)
    else:
        text = upload.getvalue().decode("utf-8-sig")
        points = load_curve_stream(StringIO(text, newline=""))
    if any(p.depth_mm < 0 or p.value < 0 for p in points):
        raise CurveDataError("Depth and relative dose values must be non-negative.")
    return points


def load_or_stop(upload, role):
    """Stop before rendering results so invalid inputs cannot leave stale outputs."""
    try:
        return read_points(upload)
    except UnicodeDecodeError:
        st.error(f"Cannot analyze {role}: export the CSV using UTF-8 encoding.")
    except (CurveDataError, OSError, csv.Error) as error:
        st.error(f"Cannot analyze {role}: {error}")
    st.stop()


def draw_curve(ax, points, peak, result, color, role, style="-"):
    """Plot each curve on its own sampled grid; do not align or resample it."""
    ax.plot([p.depth_mm for p in points], [p.value for p in points],
            color=color, linestyle=style, marker="o", linewidth=2, label=role)
    ax.scatter([peak.depth_mm], [peak.value], color=color, marker="s", zorder=4)
    if result.depth_mm is not None:
        ax.axvline(result.depth_mm, color=color, linestyle=":", alpha=0.7,
                   label=f"{role} R80: {result.depth_mm:g} mm")
        ax.scatter([result.depth_mm], [result.target_value], color=color,
                   marker="D", zorder=5)
    ax.axhline(result.target_value, color=color, linestyle="--", alpha=0.3,
               label=f"{role}: 80% of maximum")


st.set_page_config(page_title="RadQA Explorer", page_icon="📈", layout="centered")
st.title("RadQA Explorer")
st.caption("Radiation Therapy Data Visualization and QA Analytics · Reference comparison")
st.write("Explore a depth–dose curve and compare its distal R80 with a reference.")
st.caption("Educational example only. This is not a clinical QA result or patient-specific treatment guidance.")

uploaded = st.file_uploader("Upload a depth–dose CSV", type=["csv"],
                            max_upload_size=5, key="current_csv")
st.caption("Required columns: depth_mm,relative_dose_percent. UTF-8 CSV; at least two data rows; strictly increasing depths; finite, non-negative values. Maximum: 5 MB per file.")
is_uploaded = uploaded is not None
current_name = uploaded.name if is_uploaded else FIXTURE.name
current_type = "User-uploaded data" if is_uploaded else "Synthetic teaching data"
st.info(f"{current_type} — " + (
    "source and measurement validity have not been verified."
    if is_uploaded else "an illustrative example created for this project."
))
st.text(f"Current file: {current_name}")
points = load_or_stop(uploaded, "current CSV")
peak = find_peak(points)
r80 = distal_r80(points, peak)

# A reference is optional. Bundled data is explicitly synthetic, never a clinical baseline.
st.subheader("Reference curve")
reference_source = st.selectbox("Reference source", [
    "No reference", "Bundled synthetic teaching data", "Upload reference CSV",
])
reference_points = reference_peak = reference_r80 = None
reference_name = None
reference_type = None
if reference_source == "Bundled synthetic teaching data":
    reference_points = load_or_stop(None, "reference CSV")
    reference_name = FIXTURE.name
    reference_type = "Synthetic teaching data"
    st.info("Reference: Synthetic teaching data — illustrative baseline, not a measured or clinical reference.")
elif reference_source == "Upload reference CSV":
    reference_upload = st.file_uploader("Upload reference CSV", type=["csv"],
                                       max_upload_size=5, key="reference_csv")
    st.caption("Required columns: depth_mm,relative_dose_percent. The same validation rules apply to both inputs.")
    if reference_upload is not None:
        reference_points = load_or_stop(reference_upload, "reference CSV")
        reference_name = reference_upload.name
        reference_type = "User-uploaded data"
        st.info("Reference: User-uploaded data — source and measurement validity have not been verified.")
    else:
        st.info("Choose a reference CSV to enable comparison. Current-curve analysis remains available.")

if reference_points is not None:
    st.text(f"Reference file: {reference_name}")
    reference_peak = find_peak(reference_points)
    reference_r80 = distal_r80(reference_points, reference_peak)

st.subheader("Current-curve analysis")
col1, col2, col3 = st.columns(3)
col1.metric("Peak depth", f"{peak.depth_mm:g} mm")
col2.metric("Distal R80", f"{r80.depth_mm:g} mm" if r80.depth_mm is not None else "Not evaluable")
col3.metric("Peak relative dose", f"{peak.value:g}%")
if r80.depth_mm is None:
    st.warning(f"Current curve: {r80.message}")

# Keep the single-curve export available independently of comparison export.
analysis_result = {
    "input_file": current_name,
    "data_type": current_type,
    "number_of_points": len(points),
    "peak_depth_mm": peak.depth_mm,
    "peak_relative_dose_percent": peak.value,
    "distal_r80_mm": r80.depth_mm if r80.depth_mm is not None else "",
    "r80_status": r80.status,
    "r80_target_relative_dose_percent": r80.target_value,
    "r80_explanation": r80.message,
    "method": "First distal crossing of 80% of the sampled maximum; linear interpolation between adjacent samples; no extrapolation; first sampled maximum used on ties.",
    "purpose": "Educational demonstration only; not a clinical QA result or patient-specific guidance.",
}
buffer = StringIO(newline="")
writer = csv.DictWriter(buffer, fieldnames=list(analysis_result))
writer.writeheader()
writer.writerow(analysis_result)
st.download_button("Download analysis results (CSV)",
                   data=buffer.getvalue().encode("utf-8-sig"),
                   file_name="radqa_analysis_results.csv", mime="text/csv")
st.caption("Exports the current curve only, including its source, metrics, status, method, and educational-use statement.")

if reference_r80 is not None:
    reference_result = {
        "input_file": reference_name,
        "data_type": reference_type,
        "number_of_points": len(reference_points),
        "peak_depth_mm": reference_peak.depth_mm,
        "peak_relative_dose_percent": reference_peak.value,
        "distal_r80_mm": reference_r80.depth_mm if reference_r80.depth_mm is not None else "",
        "r80_status": reference_r80.status,
        "r80_target_relative_dose_percent": reference_r80.target_value,
        "r80_explanation": reference_r80.message,
    }
    comparison = comparison_record(analysis_result, reference_result)
    st.subheader("R80 comparison")
    ref_col, delta_col = st.columns(2)
    ref_col.metric("Reference distal R80", f"{reference_r80.depth_mm:g} mm"
                   if reference_r80.depth_mm is not None else "Not evaluable")
    if comparison["comparison_status"] == "ok":
        delta = comparison["delta_r80_mm"]
        delta_col.metric("ΔR80 (current − reference)", f"{delta:+g} mm")
        st.caption("Positive ΔR80 means the current curve crosses its 80% target at a greater depth than the reference.")
    else:
        delta_col.metric("ΔR80 (current − reference)", "Not evaluable")
        st.warning("ΔR80 cannot be evaluated because at least one curve has no evaluable distal R80.")
    if reference_r80.depth_mm is None:
        st.warning(f"Reference curve: {reference_r80.message}")
    st.caption("Both inputs must use the same depth origin, coordinate convention, and units. Each R80 uses 80% of its own maximum. This difference has no clinical pass/fail interpretation.")
    if points[-1].depth_mm < reference_points[0].depth_mm or reference_points[-1].depth_mm < points[0].depth_mm:
        st.warning("The sampled depth ranges do not overlap. Review the coordinate origins before interpreting the difference.")

    # Generate fresh bytes on every rerun; no previous comparison is cached.
    st.download_button(
        "Download comparison results (CSV)",
        data=csv_bytes(comparison),
        file_name="radqa_comparison_results.csv", mime="text/csv",
    )
    st.caption("Exports both source files, data types, peak/R80 metrics, ΔR80, statuses, reasons, method, and educational-use statement. Unevaluable numeric results are blank; zero remains a valid result.")

fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
draw_curve(ax, points, peak, r80, "#2563eb", "Current")
maximum = peak.value
if reference_points is not None:
    draw_curve(ax, reference_points, reference_peak, reference_r80,
               "#d97706", "Reference", "--")
    maximum = max(maximum, reference_peak.value)
ax.set(title="Depth–dose curve comparison" if reference_points is not None else "Depth–dose curve",
       xlabel="Depth (mm)", ylabel="Relative dose (%)", ylim=(0, max(1, maximum * 1.12)))
ax.grid(alpha=0.2)
ax.legend(fontsize=8, loc="best")
st.pyplot(fig)
plt.close(fig)

with st.expander("How these values are calculated"):
    st.write("Peak depth is the first sample attaining the maximum. Distal R80 is the first descending crossing of 80% of that maximum after the peak, using linear interpolation only within a sampled bracket. If the maximum is nonpositive or no crossing exists, R80 is not evaluable.")
    st.write("ΔR80 = current distal R80 − reference distal R80. The program does not automatically normalize, shift, align, or resample either curve. The two curves may use different depth sampling grids.")
    st.caption("Displayed values do not establish measurement precision. Synthetic examples do not validate real proton beams.")

with st.expander("View the input data"):
    st.write("Current curve")
    st.table({"Depth (mm)": [p.depth_mm for p in points],
              "Relative dose (%)": [p.value for p in points]})
    if reference_points is not None:
        st.write("Reference curve")
        st.table({"Depth (mm)": [p.depth_mm for p in reference_points],
                  "Relative dose (%)": [p.value for p in reference_points]})
