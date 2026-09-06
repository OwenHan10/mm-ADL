# mm-ADL Data Format

## Overview

mm-ADL is released as complete, synchronized recording runs rather than as
pre-segmented fixed-length samples. This design lets users select their own
radar-frame alignment, temporal window length, stride, label-assignment rule,
and evaluation protocol.

Each recording run is a three-file unit:

1. `radar_data.csv` contains millimeter-wave radar point-cloud observations.
2. `frame_labels.csv` contains activity annotations in the synchronized camera-frame domain.
3. `timestamps.csv` maps camera-frame indices to Unix timestamps and provides
   the temporal bridge from camera-derived annotations to radar frames.

The synchronized RGB videos used for annotation are not distributed.

## Directory structure

```text
mm-ADL-v1.0/
├── README.md
├── DATASET_CARD.md
├── DATA_FORMAT.md
├── LICENSE-DATA
├── CITATION.cff
├── SHA256SUMS.txt
├── recordings/
│   └── sub-XX/
│       └── protocol-{walk|sit|lie|fall}/
│           └── run-YY/
│               ├── radar_data.csv
│               ├── frame_labels.csv
│               └── timestamps.csv
├── metadata/
│   ├── file_schemas.csv
│   ├── label_taxonomy.csv
│   ├── protocol_definitions.csv
│   ├── recording_manifest.csv
│   └── radar_configuration/
│       └── <radar-configuration-file>.cfg
└── scripts/
    └── align_camera_labels_to_radar.py
```

`sub-XX` is a pseudonymous participant identifier. `protocol-*` identifies the
collection protocol; it is not necessarily a single frame-level activity class.
`run-YY` identifies a recording run. Multiple runs for one participant and
protocol are continuations of that collection protocol, not distinct activity
classes.

## Collection protocols

The collection protocols are defined in `metadata/protocol_definitions.csv`.
In brief:

- **walk:** approximately five minutes of random wandering with random turns and halts;
- **sit:** a chair-sitting sequence, repeated approximately 50 times, with
  front, left-side, and right-side views relative to the sensor;
- **lie:** a bed- or sofa-lying sequence, repeated approximately 50 times, with
  left-side and right-side views relative to the sensor; and
- **fall:** a fall-and-recovery sequence, repeated approximately 50 times, with
  front, left-side, and right-side views relative to the sensor.

For the sit, lie, and fall protocols, repetitions are distributed approximately
evenly across the stated orientations. “Left side facing the sensor” and “right
side facing the sensor” mean that the sensor observes the corresponding side of
the participant’s body, rather than a front-facing view.

## Recording files

### `radar_data.csv`

Each row represents one detected radar point. The point-cloud fields are:

| Column | Unit | Meaning |
|---|---:|---|
| `Frame Number` | dimensionless | Radar processing-frame index. Points detected in the same radar processing frame share this value. |
| `X` | m | Lateral (cross-range) coordinate in the radar Cartesian frame. |
| `Y` | m | Forward-range (depth) coordinate in the radar Cartesian frame. |
| `Z` | m | Vertical (elevation) coordinate in the radar Cartesian frame. |
| `velocity` | m/s | Radial Doppler velocity relative to the radar sensor. |
| `snr` | dB | Signal-to-noise ratio of the radar reflection. |
| `timestamp` | s | Unix epoch timestamp associated with the radar processing frame. |
| `target_id` | dimensionless | Target-tracker association identifier: 0–252 are tracked targets; 253–255 are noise or untracked points; and `-1` is unassigned. |

The complete radar configuration used during collection is preserved in
`metadata/radar_configuration/` as the original `.cfg` file. 

### `frame_labels.csv`

This file contains camera-frame activity annotations. It has two columns:

| Column | Unit | Meaning |
|---|---:|---|
| `Frame` | dimensionless | Camera-frame index for which an activity annotation is provided. |
| `Label` | category | Activity label assigned to that camera frame. The raw-label-to-display-name mapping is defined in `metadata/label_taxonomy.csv`. |

These labels were produced from synchronized camera recordings. They are not
direct radar annotations and must be mapped to radar frames through
`timestamps.csv` before radar-window construction.

### `timestamps.csv`

This file maps camera frames to their acquisition time. It has two columns:

| Column | Unit | Meaning |
|---|---:|---|
| `Frame` | dimensionless | Camera-frame index. |
| `Timestamp` | s | Unix epoch timestamp associated with that camera frame. |

## Mapping camera-derived labels to radar frames

The camera and radar recordings use separate frame indices but share a common
Unix-time reference. To derive labelled radar frames:

1. Read each annotation from `frame_labels.csv`, retaining its camera-frame
   index and raw label.
2. Look up the corresponding camera timestamp in `timestamps.csv`.
3. Match that timestamp to the radar processing frame(s) in `radar_data.csv`
   using the `timestamp` column. Use and report a deterministic matching rule,
   such as nearest timestamp within a declared tolerance.
4. Assign the resulting label to the matched radar frame(s), then construct
   temporal windows using a window length, stride, and window-label rule that
   are declared for the downstream task.

The release does not impose a fixed windowing scheme. 

## Labels and metadata

`metadata/label_taxonomy.csv` defines the numeric class identifier, raw label
stored in `frame_labels.csv`, paper-facing display name, description, and the
collection protocols in which each class appears. The four collection protocols
must not be confused with this ten-class frame-level taxonomy.

`metadata/recording_manifest.csv` lists all released runs and their
participant, protocol, run identifier, original folder name, and release path.

`metadata/file_schemas.csv` is the machine-readable counterpart to the column
descriptions in this document.

## Recommended validation

Before processing a recording run, verify that all three required CSV files are
present, that the frame indices used by `frame_labels.csv` occur in
`timestamps.csv`, and that the camera and radar timestamp ranges overlap.
The supplied `scripts/verify_dataset.py` and
`scripts/align_camera_labels_to_radar.py` are intended to provide the reference
implementation for these checks and the alignment procedure.
