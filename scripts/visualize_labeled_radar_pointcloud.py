#!/usr/bin/env python3
"""
visualize_labeled_radar_pointcloud.py

Animate the labeled mmWave radar point cloud of one mm-ADL recording run,
frame by frame, in 3D.

This script reads the labeled radar file produced by
``align_video_labels_to_radar.py``, so run that script first.

Expected input (<DATASET_ROOT> is the release folder, e.g. mm-ADL-v1.0):

    <DATASET_ROOT>/derived/camera_to_radar_labels/sub-XX/protocol-<name>/run-YY/
        radar_data_labeled.csv

Required columns: Frame Number, X, Y, Z, target_id, Label.
(velocity, snr and timestamp may be present but are not used.)

Point colors:
    blue - points of the dominant target in the frame, i.e. the most common
           target_id within the valid track range [0, 252]
    red  - all other points (target_id 253-255, or other targets)

Usage:
    python visualize_labeled_radar_pointcloud.py --dataset-root /path/to/mm-ADL-v1.0 \
        --subject sub-01 --protocol protocol-fall --run run-01
"""

import argparse
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Location of the labeled files inside the release root
# (must match the output of align_video_labels_to_radar.py).
LABELED_DIR = Path("derived") / "camera_to_radar_labels"
LABELED_FILENAME = "radar_data_labeled.csv"

REQUIRED_COLUMNS = ["Frame Number", "X", "Y", "Z", "target_id", "Label"]

# Valid target IDs assigned by the radar tracker. IDs outside this range
# (253-255) mark points that are not associated with any tracked target.
VALID_TID_MIN = 0
VALID_TID_MAX = 252

# Radar marker: the radar is placed at the origin of the coordinate system.
RADAR_POSITION = (0, 0, 0)
RADAR_MARKER_SIZE = 100
RADAR_COLOR = (0, 1.0, 0, 0.8)  # light green with transparency

# Fixed axis limits in meters.
X_LIM = [-6, 6]
Y_LIM = [0, 6]
Z_LIM = [-1.5, 1.5]

# Initial viewing angle.
VIEW_ELEV = 10
VIEW_AZIM = 300


def get_default_input_path(dataset_root, subject, protocol, run):
    """Return the labeled radar file of one run, e.g.
    <dataset_root>/derived/camera_to_radar_labels/sub-01/protocol-fall/run-01/
        radar_data_labeled.csv
    """
    return Path(dataset_root) / LABELED_DIR / subject / protocol / run / LABELED_FILENAME


def load_labeled_radar_data(input_path):
    """Load the labeled radar CSV and keep only the columns used for plotting."""
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Labeled radar file not found: {input_path}\n"
            "Run align_video_labels_to_radar.py first to generate it."
        )

    data = pd.read_csv(input_path)

    missing = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing:
        raise ValueError(f"{input_path} is missing required column(s): {', '.join(missing)}")
    if data.empty:
        raise ValueError(f"{input_path} contains no radar points.")

    return data[REQUIRED_COLUMNS]


def assign_point_colors(target_ids):
    """Color the dominant valid target blue and every other point red."""
    valid_tids = [tid for tid in target_ids if VALID_TID_MIN <= tid <= VALID_TID_MAX]

    # No valid target in this frame: every point is treated as noise.
    if not valid_tids:
        return ["red"] * len(target_ids)

    dominant_tid = Counter(valid_tids).most_common(1)[0][0]
    return ["blue" if tid == dominant_tid else "red" for tid in target_ids]


def format_frame_number(frame_number):
    """Show integer-valued frame numbers without a trailing '.0'."""
    if float(frame_number).is_integer():
        return str(int(frame_number))
    return str(frame_number)


def draw_frame(ax, frame_number, frame_data):
    """Draw the point cloud of a single radar frame."""
    ax.clear()

    colors = assign_point_colors(frame_data["target_id"].tolist())
    ax.scatter(frame_data["X"], frame_data["Y"], frame_data["Z"], c=colors, marker="o")

    # Radar position and a dashed vertical line from the radar to the floor.
    ax.scatter(*RADAR_POSITION, color=RADAR_COLOR, marker="^",
               s=RADAR_MARKER_SIZE, label="Radar Position")
    ax.plot([RADAR_POSITION[0], RADAR_POSITION[0]],
            [RADAR_POSITION[1], RADAR_POSITION[1]],
            [RADAR_POSITION[2], Z_LIM[0]],
            color=RADAR_COLOR, linestyle="--", label="Radar Ground Line")

    # Empty scatters to add the point colors to the legend.
    ax.scatter([], [], c="blue", marker="o", label="Non-Noise Points")
    ax.scatter([], [], c="red", marker="o", label="Noise Points")

    ax.set_title(f"3D point cloud, frame {format_frame_number(frame_number)}")
    ax.set_xlabel("X-Axis (m)")
    ax.set_ylabel("Y-Axis (m)")
    ax.set_zlabel("Z-Axis (m)")
    ax.set_xlim(X_LIM)
    ax.set_ylim(Y_LIM)
    ax.set_zlim(Z_LIM)
    ax.legend()

    # Activity label of the frame (all points in a frame share the same label).
    activity = frame_data["Label"].iloc[0]
    ax.text2D(0.05, 0.95, f"Activity: {activity}", transform=ax.transAxes,
              fontsize=10, color="blue")


def animate_point_cloud(data, interval_ms):
    """Play all frames of the run as a looping 3D animation."""
    grouped = data.groupby("Frame Number")
    frame_numbers = sorted(grouped.groups.keys())

    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.view_init(elev=VIEW_ELEV, azim=VIEW_AZIM)

    def update(frame_number):
        draw_frame(ax, frame_number, grouped.get_group(frame_number))

    # Keep a reference to the animation so it is not garbage-collected.
    animation = FuncAnimation(fig, update, frames=frame_numbers,
                              interval=interval_ms, repeat=True)
    plt.show()
    return animation


def parse_args():
    parser = argparse.ArgumentParser(
        description="Animate the labeled radar point cloud of one mm-ADL recording run."
    )
    parser.add_argument("--dataset-root", default=None,
                        help="Path to the mm-ADL release folder, e.g. /path/to/mm-ADL-v1.0")
    parser.add_argument("--subject", default="sub-01", help="Subject ID, e.g. sub-01")
    parser.add_argument("--protocol", default="protocol-fall", help="Protocol name, e.g. protocol-fall")
    parser.add_argument("--run", default="run-01", help="Run ID, e.g. run-01")
    parser.add_argument("--input", default=None,
                        help="Path to a labeled radar CSV file. Overrides --dataset-root, "
                             "--subject, --protocol and --run.")
    parser.add_argument("--interval", type=int, default=1,
                        help="Delay between frames in milliseconds (default: 1)")
    args = parser.parse_args()

    if args.input is None and args.dataset_root is None:
        parser.error("either --dataset-root or --input is required.")
    return args


def main():
    args = parse_args()

    input_path = args.input or get_default_input_path(
        args.dataset_root, args.subject, args.protocol, args.run
    )
    print(f"Input file: {input_path}")

    data = load_labeled_radar_data(input_path)
    animate_point_cloud(data, args.interval)


if __name__ == "__main__":
    main()
