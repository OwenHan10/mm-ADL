#!/usr/bin/env python3
"""Project camera-frame activity annotations onto mm-ADL radar point clouds.

The mm-ADL release preserves each acquisition run as three synchronized files:

    recordings/sub-XX/protocol-<name>/run-YY/
        radar_data.csv
        frame_labels.csv
        timestamps.csv

``frame_labels.csv`` stores activity-boundary annotations in the camera-frame
domain. ``timestamps.csv`` maps camera frames to Unix timestamps, while
``radar_data.csv`` contains timestamps for radar processing frames. This script
uses the shared timestamps to add a ``Label`` column to the radar points.

By default, derived files are written outside the raw recording tree:

    derived/camera_to_radar_labels/sub-XX/protocol-<name>/run-YY/
        radar_data_labeled.csv

The source files are never modified.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


LOGGER = logging.getLogger(__name__)

RADAR_FILENAME = "radar_data.csv"
LABEL_FILENAME = "frame_labels.csv"
TIMESTAMP_FILENAME = "timestamps.csv"
OUTPUT_FILENAME = "radar_data_labeled.csv"

RADAR_REQUIRED_COLUMNS = {"Frame Number", "timestamp"}
LABEL_REQUIRED_COLUMNS = {"Frame", "Label"}
TIMESTAMP_REQUIRED_COLUMNS = {"Frame", "Timestamp"}

END_LABEL = "END"
DELETE_LABEL = "DELETE"


@dataclass(frozen=True)
class RecordingPaths:
    """Input and output paths associated with one mm-ADL recording run."""

    input_directory: Path
    output_file: Path


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Project camera-frame mm-ADL annotations onto radar point clouds "
            "for one recording run or an entire release."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--dataset-root",
        type=Path,
        help=(
            "Path to the mm-ADL release root containing the recordings/ "
            "directory. All matching recording runs are processed."
        ),
    )
    source_group.add_argument(
        "--recording-dir",
        type=Path,
        help=(
            "Path to one recording directory containing radar_data.csv, "
            "frame_labels.csv, and timestamps.csv."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Root directory for derived labelled files. With --dataset-root, "
            "the default is <dataset-root>/derived/camera_to_radar_labels. "
            "This option is required with --recording-dir."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing derived radar_data_labeled.csv file.",
    )
    parser.add_argument(
        "--allow-missing-label-timestamps",
        action="store_true",
        help=(
            "Skip annotation intervals whose camera-frame timestamps are "
            "missing instead of stopping with an error."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed processing information.",
    )
    return parser.parse_args()


def validate_columns(dataframe: pd.DataFrame, required: set[str], filename: Path) -> None:
    """Raise a clear error when a required input column is absent."""
    missing = required.difference(dataframe.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"{filename} is missing required column(s): {missing_text}")


def read_recording(recording_directory: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and validate the three synchronized CSV files for one run."""
    radar_path = recording_directory / RADAR_FILENAME
    labels_path = recording_directory / LABEL_FILENAME
    timestamps_path = recording_directory / TIMESTAMP_FILENAME

    for input_path in (radar_path, labels_path, timestamps_path):
        if not input_path.is_file():
            raise FileNotFoundError(f"Required input file not found: {input_path}")

    radar_data = pd.read_csv(radar_path)
    frame_labels = pd.read_csv(labels_path)
    camera_timestamps = pd.read_csv(timestamps_path)

    validate_columns(radar_data, RADAR_REQUIRED_COLUMNS, radar_path)
    validate_columns(frame_labels, LABEL_REQUIRED_COLUMNS, labels_path)
    validate_columns(camera_timestamps, TIMESTAMP_REQUIRED_COLUMNS, timestamps_path)

    if camera_timestamps["Frame"].duplicated().any():
        raise ValueError(f"{timestamps_path} contains duplicate camera-frame indices.")

    for dataframe, column, path in (
        (radar_data, "timestamp", radar_path),
        (camera_timestamps, "Timestamp", timestamps_path),
    ):
        dataframe[column] = pd.to_numeric(dataframe[column], errors="raise")

    return radar_data, frame_labels, camera_timestamps


def build_label_intervals(
    frame_labels: pd.DataFrame,
    camera_timestamps: pd.DataFrame,
    *,
    allow_missing_timestamps: bool,
) -> pd.DataFrame:
    """Convert camera-frame label boundaries into timestamp intervals.

    Each row in ``frame_labels.csv`` marks the start of a label interval. Its
    end is the timestamp of the next annotation row. ``END`` terminates the
    recording, and ``DELETE`` identifies an interval to omit from the derived
    output. A final non-END label extends to the end of the radar recording.
    """
    camera_timestamp_by_frame = camera_timestamps.set_index("Frame")["Timestamp"].to_dict()
    annotation_rows = list(frame_labels[["Frame", "Label"]].itertuples(index=False, name=None))
    intervals: list[dict[str, object]] = []

    for index, (start_frame, label) in enumerate(annotation_rows):
        label = str(label)
        if label == END_LABEL:
            break

        if start_frame not in camera_timestamp_by_frame:
            message = (
                f"Annotation frame {start_frame!r} has no timestamp in "
                "timestamps.csv."
            )
            if allow_missing_timestamps:
                LOGGER.warning("Skipping interval: %s", message)
                continue
            raise ValueError(message)

        start_time = camera_timestamp_by_frame[start_frame]
        if index + 1 < len(annotation_rows):
            next_frame, _ = annotation_rows[index + 1]
            if next_frame not in camera_timestamp_by_frame:
                message = (
                    f"Annotation frame {next_frame!r} has no timestamp in "
                    "timestamps.csv."
                )
                if allow_missing_timestamps:
                    LOGGER.warning("Skipping interval: %s", message)
                    continue
                raise ValueError(message)
            end_time = camera_timestamp_by_frame[next_frame]
        else:
            end_time = float("inf")

        if end_time <= start_time:
            raise ValueError(
                "Annotation timestamps must increase strictly; found "
                f"interval [{start_time}, {end_time}) for frame {start_frame!r}."
            )

        intervals.append(
            {"start_time": start_time, "end_time": end_time, "Label": label}
        )

    if not intervals:
        raise ValueError("No valid label intervals were constructed from frame_labels.csv.")

    return pd.DataFrame(intervals).sort_values("start_time").reset_index(drop=True)


def assign_labels_to_radar_points(
    radar_data: pd.DataFrame, label_intervals: pd.DataFrame
) -> pd.DataFrame:
    """Assign each radar point the label of its enclosing timestamp interval."""
    radar_timestamps = radar_data[["timestamp"]].copy()
    radar_timestamps["_original_row"] = range(len(radar_timestamps))
    radar_timestamps = radar_timestamps.sort_values("timestamp")

    matched = pd.merge_asof(
        radar_timestamps,
        label_intervals,
        left_on="timestamp",
        right_on="start_time",
        direction="backward",
    )

    valid = (
        matched["Label"].notna()
        & (matched["timestamp"] < matched["end_time"])
        & (matched["Label"] != DELETE_LABEL)
    )
    matched = matched.loc[valid, ["_original_row", "Label"]].sort_values("_original_row")

    labelled_radar_data = radar_data.iloc[matched["_original_row"].to_numpy()].copy()
    labelled_radar_data["Label"] = matched["Label"].to_numpy()
    return labelled_radar_data


def discover_recordings(dataset_root: Path, output_root: Path) -> Iterable[RecordingPaths]:
    """Find all release-format recording directories and preserve their layout."""
    recordings_root = dataset_root / "recordings"
    if not recordings_root.is_dir():
        raise FileNotFoundError(f"Recordings directory not found: {recordings_root}")

    recording_directories = sorted(
        path
        for path in recordings_root.glob("sub-*/protocol-*/run-*")
        if path.is_dir()
    )
    if not recording_directories:
        raise FileNotFoundError(
            "No recording directories matching "
            "recordings/sub-*/protocol-*/run-* were found."
        )

    for recording_directory in recording_directories:
        relative_recording_path = recording_directory.relative_to(recordings_root)
        yield RecordingPaths(
            input_directory=recording_directory,
            output_file=output_root / relative_recording_path / OUTPUT_FILENAME,
        )


def process_recording(
    paths: RecordingPaths, *, overwrite: bool, allow_missing_timestamps: bool
) -> None:
    """Create one labelled radar-point CSV without altering the raw inputs."""
    if paths.output_file.exists() and not overwrite:
        LOGGER.info("Skipping existing output: %s", paths.output_file)
        return

    radar_data, frame_labels, camera_timestamps = read_recording(paths.input_directory)
    label_intervals = build_label_intervals(
        frame_labels,
        camera_timestamps,
        allow_missing_timestamps=allow_missing_timestamps,
    )
    labelled_radar_data = assign_labels_to_radar_points(radar_data, label_intervals)

    paths.output_file.parent.mkdir(parents=True, exist_ok=True)
    labelled_radar_data.to_csv(paths.output_file, index=False)
    LOGGER.info(
        "Wrote %d labelled points from %s to %s",
        len(labelled_radar_data),
        paths.input_directory,
        paths.output_file,
    )


def main() -> None:
    """Run the camera-to-radar label projection workflow."""
    args = parse_arguments()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.dataset_root is not None:
        dataset_root = args.dataset_root.resolve()
        output_root = (
            args.output_root.resolve()
            if args.output_root is not None
            else dataset_root / "derived" / "camera_to_radar_labels"
        )
        recordings = discover_recordings(dataset_root, output_root)
    else:
        if args.output_root is None:
            raise ValueError("--output-root is required when using --recording-dir.")
        recording_directory = args.recording_dir.resolve()
        output_root = args.output_root.resolve()
        recordings = [
            RecordingPaths(
                input_directory=recording_directory,
                output_file=output_root / recording_directory.name / OUTPUT_FILENAME,
            )
        ]

    processed_count = 0
    for recording_paths in recordings:
        process_recording(
            recording_paths,
            overwrite=args.overwrite,
            allow_missing_timestamps=args.allow_missing_label_timestamps,
        )
        processed_count += 1

    LOGGER.info("Processed %d recording run(s).", processed_count)


if __name__ == "__main__":
    main()
