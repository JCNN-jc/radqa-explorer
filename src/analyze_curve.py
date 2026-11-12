#!/usr/bin/env python3
"""Validate a depth-dose CSV and calculate peak depth and distal R80.

The built-in fixture is synthetic teaching data. Its distal R80 convention is
80% of the discrete maximum on the descending branch after the peak, with
piecewise-linear interpolation. This is not clinical analysis software.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence, TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Resolve the fixture from this file so the command works from any working directory.
DEFAULT_FIXTURE = PROJECT_ROOT / "data" / "fixtures" / "day3_handcheck_curve.csv"
REQUIRED_COLUMNS = ("depth_mm", "relative_dose_percent")


class CurveDataError(ValueError):
    """Raised when the input CSV cannot be analyzed without guessing."""


@dataclass(frozen=True)
class Point:
    depth_mm: float
    value: float
    row_number: int


@dataclass(frozen=True)
class R80Result:
    status: str
    depth_mm: float | None
    target_value: float
    message: str
    segment_depths_mm: tuple[float, float] | None = None


def load_curve(path: Path) -> list[Point]:
    """Load and validate required fields; never sort or silently drop rows."""
    try:
        handle = path.open("r", newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise CurveDataError(f"Cannot open '{path}': {exc}") from exc

    with handle:
        return load_curve_stream(handle)


def load_curve_stream(handle: TextIO) -> list[Point]:
    """Validate text from either a disk CSV or an in-memory uploaded CSV."""
    reader = csv.reader(handle)
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise CurveDataError("The CSV file is empty; it has no header row.") from exc

    # utf-8-sig above also handles spreadsheets that add a byte-order mark.
    if not headers or all(not name.strip() for name in headers):
        raise CurveDataError("The CSV header row is empty.")
    if len(set(headers)) != len(headers):
        raise CurveDataError("The CSV contains duplicate column names.")
    missing = [name for name in REQUIRED_COLUMNS if name not in headers]
    if missing:
        raise CurveDataError(
            "Missing required column(s): " + ", ".join(missing)
            + ". Expected: depth_mm and relative_dose_percent."
        )

    depth_index = headers.index("depth_mm")
    value_index = headers.index("relative_dose_percent")
    points: list[Point] = []
    previous_depth: float | None = None

    for row_number, row in enumerate(reader, start=2):
        if not row or all(not cell.strip() for cell in row):
            raise CurveDataError(f"Row {row_number} is blank; remove it or fill it explicitly.")
        if len(row) != len(headers):
            raise CurveDataError(
                f"Row {row_number} has {len(row)} fields; expected {len(headers)}."
            )
        raw_depth, raw_value = row[depth_index].strip(), row[value_index].strip()
        if not raw_depth or not raw_value:
            raise CurveDataError(
                f"Row {row_number} is missing depth_mm or relative_dose_percent."
            )
        try:
            depth, value = float(raw_depth), float(raw_value)
        except ValueError as exc:
            raise CurveDataError(
                f"Row {row_number} has a non-numeric depth or dose value."
            ) from exc
        # NaN and infinity pass float() but make ordering and interpolation unreliable.
        if not math.isfinite(depth) or not math.isfinite(value):
            raise CurveDataError(
                f"Row {row_number} contains NaN or infinity; values must be finite."
            )
        if previous_depth is not None:
            # Input order defines the distal branch; sorting here could hide a data issue.
            if depth == previous_depth:
                raise CurveDataError(
                    f"Row {row_number} repeats depth {depth:g} mm. Resolve duplicates explicitly."
                )
            if depth < previous_depth:
                raise CurveDataError(
                    f"Depths are not increasing at row {row_number} ({depth:g} mm follows "
                    f"{previous_depth:g} mm). The script does not reorder input data."
                )
        points.append(Point(depth, value, row_number))
        previous_depth = depth

    if len(points) < 2:
        raise CurveDataError("At least two valid data points are required.")
    return points


def find_peak(points: Sequence[Point]) -> Point:
    """Return the first point attaining the maximum value."""
    # max() preserves the first point on ties, making plateau handling deterministic.
    return max(points, key=lambda point: point.value)


def distal_r80(points: Sequence[Point], peak: Point) -> R80Result:
    """Find the first 80%-of-maximum crossing after peak, without extrapolating."""
    maximum = peak.value
    if maximum <= 0:
        return R80Result(
            status="not_evaluable",
            depth_mm=None,
            target_value=0.8 * maximum,
            message="The curve maximum must be positive to define this R80 convention.",
        )

    target = 0.8 * maximum
    peak_index = points.index(peak)
    # Only inspect samples after the peak; an entrance-side crossing is not distal R80.
    for left, right in zip(points[peak_index:], points[peak_index + 1 :]):
        # Require an actual descending segment; an exact target point also counts.
        if left.value == target:
            return R80Result(
                "ok", left.depth_mm, target, "R80 equals a sampled point on the distal branch.",
                (left.depth_mm, left.depth_mm),
            )
        if left.value > target and right.value == target:
            return R80Result(
                "ok", right.depth_mm, target, "R80 equals a sampled point on the distal branch.",
                (left.depth_mm, right.depth_mm),
            )
        if left.value > target > right.value:
            # Interpolate only inside a sampled descending segment that brackets the target.
            depth = left.depth_mm + (target - left.value) * (
                right.depth_mm - left.depth_mm
            ) / (right.value - left.value)
            return R80Result(
                "ok", depth, target,
                "First distal crossing after the peak; linearly interpolated between samples.",
                (left.depth_mm, right.depth_mm),
            )

    # A missing bracket means the available data do not support an R80 estimate.
    return R80Result(
        status="not_evaluable",
        depth_mm=None,
        target_value=target,
        message="No distal 80% crossing is present after the peak; no extrapolation was made.",
    )


def analyze(path: Path, data_type: str) -> dict[str, object]:
    points = load_curve(path)
    peak = find_peak(points)
    r80 = distal_r80(points, peak)
    return {
        # Keep provenance and the chosen convention next to the numerical outputs.
        "input_file": path.name,
        "data_type": data_type,
        "curve_convention": "80% of maximum on descending branch after peak; piecewise-linear crossing",
        "number_of_points": len(points),
        "peak_depth_mm": peak.depth_mm,
        "peak_value": peak.value,
        "distal_R80": asdict(r80),
        "clinical_use": "educational demonstration only; not patient-specific or clinical QA guidance",
    }


def run_self_check() -> None:
    """Check the known-answer CSV and a no-crossing case without external packages."""
    points = load_curve(DEFAULT_FIXTURE)
    peak = find_peak(points)
    r80 = distal_r80(points, peak)
    # These expected values were calculated by hand from the bundled fixture.
    assert peak.depth_mm == 10.0 and peak.value == 100.0, "Fixture peak should be 100% at 10 mm."
    assert r80.status == "ok" and math.isclose(r80.depth_mm or math.nan, 11.0), (
        "Fixture distal R80 should be 11 mm."
    )

    # Deliberately stop above 80% to verify that the code does not extrapolate.
    truncated_curve = [Point(0, 10, 2), Point(1, 100, 3), Point(2, 90, 4)]
    unavailable = distal_r80(truncated_curve, find_peak(truncated_curve))
    assert unavailable.status == "not_evaluable" and unavailable.depth_mm is None, (
        "A missing distal crossing must not be extrapolated."
    )
    print("PASS: fixture peak = 10 mm; distal R80 = 11 mm; missing crossing = not evaluable.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a depth-dose CSV and calculate peak depth and distal R80."
    )
    parser.add_argument(
        "csv_file", nargs="?", type=Path, default=DEFAULT_FIXTURE,
        help="Input CSV (default: bundled synthetic hand-check fixture).",
    )
    parser.add_argument(
        "--data-type", choices=("synthetic", "reference", "measured"), default=None,
        help="Provenance label. Defaults to synthetic for the bundled fixture; otherwise required.",
    )
    parser.add_argument(
        "--self-check", action="store_true",
        help="Run known-answer and no-extrapolation checks, then exit.",
    )
    args = parser.parse_args(argv)

    if args.self_check:
        try:
            run_self_check()
        except (AssertionError, CurveDataError) as exc:
            print(f"SELF-CHECK FAILED: {exc}", file=sys.stderr)
            return 1
        return 0

    data_type = args.data_type
    if data_type is None:
        # Non-fixture inputs need an explicit label so reports do not imply provenance.
        if args.csv_file.resolve() == DEFAULT_FIXTURE.resolve():
            data_type = "synthetic"
        else:
            parser.error("--data-type is required for a CSV other than the bundled fixture.")

    try:
        result = analyze(args.csv_file, data_type)
    except CurveDataError as exc:
        print(f"DATA ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
