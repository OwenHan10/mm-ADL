# mm-ADL Data Format

This document specifies the recording layout, CSV fields, and camera-to-radar
label alignment. For an overview, download link, usage commands, and citation,
see [README.md](README.md).

## Recording layout

```text
recordings/sub-XX/protocol-{walk|sit|lie|fall}/run-YY/
├── radar_data.csv
├── frame_labels.csv
└── timestamps.csv
```

`sub-XX` is a pseudonymous participant identifier. `protocol-*` identifies the
collection protocol.
`run-YY` identifies a recording run. Multiple runs for one participant and
protocol are continuations of that collection protocol, not distinct activity
classes.

Protocol definitions and collection details are in
`metadata/protocol_definitions.csv`. Protocol names are not frame-level class
labels.

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

This file contains camera-frame activity annotation boundaries, not a label
for every radar point. It has two columns:

| Column | Unit | Meaning |
|---|---:|---|
| `Frame` | dimensionless | Camera-frame index at which an annotated segment starts. |
| `Label` | category | Raw label for that segment. The raw-label-to-display-name mapping is in `metadata/label_taxonomy.csv`. |

These labels were produced from synchronized camera recordings. They are not
direct radar annotations and must be mapped to radar frames through
`timestamps.csv` before radar-window construction.

### `timestamps.csv`

This file maps camera frames to their acquisition time. It has two columns:

| Column | Unit | Meaning |
|---|---:|---|
| `Frame` | dimensionless | Camera-frame index. |
| `Timestamp` | s | Unix epoch timestamp associated with that camera frame. |

## Mapping camera-derived labels to radar points

The camera and radar recordings use separate frame indices but share a common
Unix-time reference. The provided alignment scripts implement the following
interval rule:

1. Look up each annotated boundary frame's Unix time in `timestamps.csv`.
2. Assign label `i` to the half-open interval from its boundary timestamp up
   to, but not including, the next annotation boundary timestamp.
3. Assign the interval's label to each radar point whose `timestamp` falls in
   that interval. Drop points outside labeled intervals and points in a
   `DELETE` interval. An `END` boundary terminates labeling; points from that
   boundary onward are dropped.
4. If the final boundary is neither `END` nor missing from `timestamps.csv`,
   its label extends through the remaining radar data. The output preserves
   the radar columns and appends `Label`.

The derived output is written under
`derived/camera_to_radar_labels/sub-XX/protocol-<name>/run-YY/radar_data_labeled.csv`.
The raw CSVs are unchanged. The release does not impose a fixed temporal
windowing or window-label rule; report those choices in downstream work.

## Labels and metadata

`metadata/label_taxonomy.csv` defines the numeric class identifier, raw label
stored in `frame_labels.csv`, paper-facing display name, description, and the
collection protocols in which each class appears. The four collection protocols
must not be confused with this ten-class frame-level taxonomy.

`metadata/recording_manifest.csv` lists all released runs and their
participant, protocol, run identifier, original folder name, and release path.

`metadata/file_schemas.csv` is the machine-readable counterpart to the column
descriptions in this document. The radar acquisition `.cfg` is in
`metadata/radar_configuration/`.

