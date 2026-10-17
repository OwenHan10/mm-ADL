"""
align_video_labels_to_radar.py

Transfer activity labels annotated on the RGB video to the mmWave radar
point cloud data of the mm-ADL dataset.

The annotation was originally performed on the RGB video. Each recording
run contains three files:

    frame_labels.csv  - columns: Frame, Label
                        Each row marks the video frame at which a new label
                        starts. Special labels:
                          DELETE : segment is discarded
                          END    : this frame and everything after it is discarded
    timestamps.csv    - columns: Frame, Timestamp
                        Unix timestamp of every video frame.
    radar_data.csv    - columns: Frame Number, X, Y, Z, velocity, snr,
                        timestamp, target_id
                        Radar point cloud, one row per point.

Each radar point is assigned the label of the video segment whose time
interval [start_time, end_time) contains the point's timestamp. Points that
fall outside every labeled segment, inside a DELETE segment, or after END are
dropped.

Expected dataset layout (<DATASET_ROOT> is the release folder, e.g. mm-ADL-v1.0):

    <DATASET_ROOT>/recordings/sub-XX/protocol-<name>/run-YY/
        frame_labels.csv
        timestamps.csv
        radar_data.csv

Output (the source files are never modified):

    <DATASET_ROOT>/derived/camera_to_radar_labels/sub-XX/protocol-<name>/run-YY/
        radar_data_labeled.csv

Usage:
    python align_video_labels_to_radar.py --dataset-root /path/to/mm-ADL-v1.0 \
        --subject sub-01 --protocol protocol-fall --run run-01
"""

import argparse
from pathlib import Path

import pandas as pd

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Sub-folders inside the release root, following the published dataset structure.
RECORDINGS_DIR = "recordings"
OUTPUT_DIR = Path("derived") / "camera_to_radar_labels"
OUTPUT_FILENAME = "radar_data_labeled.csv"

# Special labels used in frame_labels.csv.
LABEL_DELETE = "DELETE"
LABEL_END = "END"


def get_run_dir(dataset_root, subject, protocol, run):
    """Return the folder of one recording run, e.g.
    <dataset_root>/recordings/sub-01/protocol-fall/run-01
    """
    return Path(dataset_root) / RECORDINGS_DIR / subject / protocol / run


def get_default_output_path(dataset_root, subject, protocol, run):
    """Return the default output CSV path, e.g.
    <dataset_root>/derived/camera_to_radar_labels/sub-01/protocol-fall/run-01/
        radar_data_labeled.csv
    """
    return Path(dataset_root) / OUTPUT_DIR / subject / protocol / run / OUTPUT_FILENAME


def build_label_intervals(frame_labels_df, video_ts_dict):
    """Convert per-frame label boundaries into time intervals.

    Consecutive rows (frame_i, label_i) and (frame_{i+1}, label_{i+1}) form the
    interval [ts(frame_i), ts(frame_{i+1})) carrying label_i.

    Args:
        frame_labels_df: DataFrame with columns Frame, Label.
        video_ts_dict:   dict mapping video frame index -> timestamp.

    Returns:
        List of dicts with keys start_time, end_time, label, sorted by start_time.
    """
    intervals = []
    labels_array = frame_labels_df.to_records(index=False)

    for i in range(len(labels_array) - 1):
        start_frame, label = labels_array[i]
        next_frame, _ = labels_array[i + 1]

        # END: this frame and all following frames are discarded.
        if label == LABEL_END:
            break

        # Skip segments whose boundary frames have no timestamp.
        if start_frame not in video_ts_dict or next_frame not in video_ts_dict:
            continue

        intervals.append({
            "start_time": video_ts_dict[start_frame],
            "end_time": video_ts_dict[next_frame],
            "label": label,
        })

    # If the last row is not END, extend its label until the end of the data.
    # A trailing DELETE segment is still added so that it can be filtered out.
    if len(labels_array) > 0:
        last_frame, last_label = labels_array[-1]
        if last_label != LABEL_END and last_frame in video_ts_dict:
            intervals.append({
                "start_time": video_ts_dict[last_frame],
                "end_time": float("inf"),
                "label": last_label,
            })

    intervals.sort(key=lambda x: x["start_time"])
    return intervals


def find_label(ts, intervals):
    """Return the label of the interval containing timestamp ts, or None."""
    for interval in intervals:
        if interval["start_time"] <= ts < interval["end_time"]:
            return interval["label"]
    return None


def label_radar_data(run_dir, output_path):
    """Label the radar point cloud of one run and save it as a CSV file."""
    run_dir = Path(run_dir)
    output_path = Path(output_path)

    print(f"Input run folder : {run_dir}")
    print(f"Output file      : {output_path}")

    # 1. Load CSV files.
    frame_labels_df = pd.read_csv(run_dir / "frame_labels.csv")  # Frame, Label
    timestamps_df = pd.read_csv(run_dir / "timestamps.csv")      # Frame, Timestamp
    radar_data_df = pd.read_csv(run_dir / "radar_data.csv")      # Frame Number, X, Y, Z, velocity, snr, timestamp, target_id

    # 2. Map video frame index to timestamp, e.g. {0: 1736614256.13, 1: 1736614256.29, ...}
    video_ts_dict = timestamps_df.set_index("Frame")["Timestamp"].to_dict()

    # 3. Build labeled time intervals from the video annotation.
    intervals = build_label_intervals(frame_labels_df, video_ts_dict)

    # 4. Assign a label to every radar point.
    output_records = []
    for _, row in radar_data_df.iterrows():
        label = find_label(row["timestamp"], intervals)

        # Drop points outside all intervals, after END, or in DELETE segments.
        if label is None or label == LABEL_DELETE:
            continue

        row_dict = row.to_dict()
        row_dict["Label"] = label
        output_records.append(row_dict)

    # 5. Keep the original column order and append the Label column at the end.
    columns = list(radar_data_df.columns)
    if "Label" not in columns:
        columns.append("Label")
    result_df = pd.DataFrame(output_records, columns=columns)

    # 6. Save the result.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    print(f"Saved {len(result_df)} labeled radar points.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transfer video-based activity labels to radar point cloud data (mm-ADL dataset)."
    )
    parser.add_argument("--dataset-root", required=True,
                        help="Path to the mm-ADL release folder containing recordings/, e.g. /path/to/mm-ADL-v1.0")
    parser.add_argument("--subject", default="sub-01", help="Subject ID, e.g. sub-01")
    parser.add_argument("--protocol", default="protocol-fall", help="Protocol name, e.g. protocol-fall")
    parser.add_argument("--run", default="run-01", help="Run ID, e.g. run-01")
    parser.add_argument("--output", default=None,
                        help="Output CSV path (default: <dataset-root>/derived/camera_to_radar_labels/"
                             "<subject>/<protocol>/<run>/radar_data_labeled.csv)")
    return parser.parse_args()


def main():
    args = parse_args()

    run_dir = get_run_dir(args.dataset_root, args.subject, args.protocol, args.run)
    output_path = args.output or get_default_output_path(
        args.dataset_root, args.subject, args.protocol, args.run
    )

    label_radar_data(run_dir, output_path)


if __name__ == "__main__":
    main()
