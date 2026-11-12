"""Serialize educational comparison results without replacing missing values by zero."""
import csv
from io import StringIO

METHOD = (
    "First distal crossing of 80% of each curve's own sampled maximum; "
    "linear interpolation between adjacent samples; no extrapolation; "
    "first sampled maximum used on ties; no automatic normalization or alignment."
)


def comparison_record(current, reference):
    """Combine the two current analysis records; zero is a valid difference."""
    fields = (
        "input_file", "data_type", "number_of_points", "peak_depth_mm",
        "peak_relative_dose_percent", "distal_r80_mm", "r80_status",
        "r80_target_relative_dose_percent", "r80_explanation",
    )
    record = {}
    for role, analysis in (("current", current), ("reference", reference)):
        for field in fields:
            record[f"{role}_{field}"] = analysis[field]

    evaluable = all(
        a["r80_status"] == "ok" and a["distal_r80_mm"] not in (None, "")
        for a in (current, reference)
    )
    record["delta_r80_mm"] = (
        current["distal_r80_mm"] - reference["distal_r80_mm"] if evaluable else ""
    )
    record["comparison_status"] = "ok" if evaluable else "not_evaluable"
    if evaluable:
        message = "Both distal R80 values are evaluable; difference calculated."
    else:
        reasons = [
            f"{role}: {a['r80_explanation']}"
            for role, a in (("Current", current), ("Reference", reference))
            if a["r80_status"] != "ok" or a["distal_r80_mm"] in (None, "")
        ]
        message = "Delta R80 not evaluable. " + " ".join(reasons)
    record["comparison_explanation"] = message
    record["delta_definition"] = "current distal R80 minus reference distal R80 (mm)"
    record["method"] = METHOD
    record["coordinate_assumption"] = "Both inputs must use the same depth origin, coordinate convention, and units; this is not verified automatically."
    record["purpose"] = "Educational demonstration only; not a clinical QA result or patient-specific guidance. No clinical pass/fail threshold is applied."
    return record


def csv_bytes(record):
    """Quote text using the CSV standard and include a BOM for Excel."""
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(record))
    writer.writeheader()
    writer.writerow(record)
    return buffer.getvalue().encode("utf-8-sig")
