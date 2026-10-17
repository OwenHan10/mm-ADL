# mm-ADL

**mm-ADL** is a millimeter-wave (mmWave) radar point-cloud dataset for activities of daily living (ADLs) and fall-related movements. It provides complete recording runs and camera-derived annotations that can be aligned to radar timestamps. Researchers can choose their own segmentation and evaluation protocols.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22405011.svg)](https://doi.org/10.5281/zenodo.22405011)
[![arXiv](https://img.shields.io/badge/arXiv-2609.08818-b31b1b.svg)](https://arxiv.org/abs/2609.08818)

## Full dataset download

Download the complete release, including the `recordings/` directory, from
[Zenodo](https://doi.org/10.5281/zenodo.22405011). The GitHub repository contains
documentation, metadata, radar configuration, and processing scripts; it does
not duplicate the recordings.

For the recording layout, CSV schemas, and alignment rules, see
[DATA_FORMAT.md](DATA_FORMAT.md).

## Associated publication

mm-ADL is introduced in the following paper:

> X. Wang, Z. Han, S. Rhanmouni, C. Zhao, Y. Lu, and M. Bolic,
> “Beyond Gait: Person Identification from Millimeter-Wave Point Clouds
> Across Activities of Daily Living,” *arXiv preprint* arXiv:2609.08818, 2026.

[Read the paper on arXiv](https://arxiv.org/abs/2609.08818)

## Dataset at a glance

| Item | Description |
|---|---|
| Participants | 11 pseudonymous participants: 6 male participants (`sub-01` to `sub-06`) and 5 female participants (`sub-07` to `sub-11`) |
| Setting | Controlled 4 m × 8 m indoor room |
| Modality | Time-series mmWave radar point clouds |
| Recording unit | Complete participant–protocol–run recording |
| Collection protocols | Walk, sit, lie, and fall |
| Frame-level classes | 10 activity and posture classes |
| Video release | Synchronized RGB video was used for annotation but is not distributed |

## Radar platform and setup

Data were acquired using the Texas Instruments (TI) **IWR6843ISK-ODS** antenna board with an **MMWAVEICBOOST** carrier board. The radar was mounted on a camera tripod at a height of approximately 1.5 m. Its boresight was perpendicular to the ground; no tilt angle was used.

The acquisition configuration is in `metadata/radar_configuration/`. The
four collection protocols are distinct from the ten frame-level classes; see
`metadata/protocol_definitions.csv` and `metadata/label_taxonomy.csv` for their
definitions.

## Repository contents

```text
mm-ADL/
├── README.md
├── DATA_FORMAT.md
├── LICENSE-DATA
├── metadata/
│   ├── recording_manifest.csv
│   ├── protocol_definitions.csv
│   ├── label_taxonomy.csv
│   ├── file_schemas.csv
│   └── radar_configuration/
│       └── <radar-configuration-file>.cfg
└── scripts/
    ├── align_camera_labels_to_radar.py
    ├── align_video_labels_to_radar.py
    └── visualize_labeled_radar_pointcloud.py
```

The full Zenodo release also contains `recordings/sub-XX/protocol-<name>/run-YY/`.
Each run has `radar_data.csv`, `frame_labels.csv`, and `timestamps.csv`; see
[DATA_FORMAT.md](DATA_FORMAT.md) for their fields and relationship.

## Label and visualize radar point clouds

Install the required Python packages (`pandas` and `matplotlib`), then run the
following commands from the repository root. The release does not include fixed
windows or directly labeled radar frames.

### Batch label alignment

`align_camera_labels_to_radar.py` processes the full release or an individual
recording directory. It leaves the raw files unchanged and writes labeled CSVs to:

```text
derived/camera_to_radar_labels/sub-XX/protocol-<name>/run-YY/radar_data_labeled.csv
```

Process the complete release:

```bash
python scripts/align_camera_labels_to_radar.py --dataset-root /path/to/mm-ADL-v1.0
```

Use `--overwrite` to regenerate existing output. For individual-recording
options, run:

```bash
python scripts/align_camera_labels_to_radar.py --help
```

### Single-recording label alignment

`align_video_labels_to_radar.py` is the original, step-by-step reference
implementation for aligning one recording run at a time. It produces the same
labeled output format as the batch script and includes more inline comments for
readers who want to understand the alignment procedure.

```bash
python scripts/align_video_labels_to_radar.py \
  --dataset-root /path/to/mm-ADL-v1.0 \
  --subject sub-01 \
  --protocol protocol-fall \
  --run run-01
```

### Visualization

`visualize_labeled_radar_pointcloud.py` animates the labeled 3D radar point
cloud of one recording run. Run either alignment script first.

```bash
python scripts/visualize_labeled_radar_pointcloud.py \
  --dataset-root /path/to/mm-ADL-v1.0 \
  --subject sub-01 \
  --protocol protocol-fall \
  --run run-01
```

The animation shows the activity label and colors the dominant tracked target
blue and other points red.

## Intended research uses

mm-ADL is intended for research on:

- mmWave radar human activity recognition;
- fall-related activity recognition;
- temporal segmentation and camera-to-radar annotation alignment;
- person identification and re-identification from radar point clouds; and
- representation learning for radar-based human sensing.

## Privacy

Participant identifiers are pseudonymous, and the synchronized camera videos used for annotation are not released. An example RGB video illustrating the experimental protocol may be made available upon request to the corresponding author of the associated study. 

## Citation

If you use the mm-ADL dataset, please cite **both** the dataset record and its
associated paper:

1. **Dataset:**  Han, Z., Wang, X., & Bolic, M. (2026). mm-ADL: A Millimeter-Wave Radar Point-Cloud Dataset for Activities of Daily Living and Fall-Related Movements [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.22405011

2. **Associated paper:**  X. Wang, Z. Han, S. Rhanmouni, C. Zhao, Y. Lu, and
   M. Bolic, “Beyond Gait: Person Identification from Millimeter-Wave Point
   Clouds Across Activities of Daily Living,” *arXiv preprint* arXiv:2609.08818, 2026. https://arxiv.org/abs/2609.08818

## License

The mm-ADL dataset is licensed under the
[Creative Commons Attribution 4.0 International License (CC BY 4.0)](
https://creativecommons.org/licenses/by/4.0/).

When using the dataset, please provide appropriate attribution and cite both the
Zenodo dataset record and the associated paper as described in the
[Citation](#citation) section.
