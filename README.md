# mm-ADL

**mm-ADL** is a synchronized millimeter-wave (mmWave) radar point-cloud dataset for activities of daily living (ADLs) and fall-related movements. It preserves complete recording runs, camera-derived frame annotations, and the timestamps needed to project those annotations to radar frames. This raw-run design lets researchers choose their own radar-frame alignment, temporal segmentation, and evaluation protocol.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22405011.svg)](https://doi.org/10.5281/zenodo.22405011)

## Full dataset download

The complete mm-ADL release, including all raw recording runs, is hosted on
[Zenodo](https://doi.org/10.5281/zenodo.22405011).

This GitHub repository provides the documentation, metadata, radar configuration,
and reference processing scripts. It does not duplicate the full `recordings/`
directory.

## Dataset at a glance

| Item | Description |
|---|---|
| Participants | 11 pseudonymous participants: 6 male participants (`sub-01` to `sub-06`) and 5 female participants (`sub-07` to `sub-11`) |
| Setting | Controlled 4 m × 8 m indoor room |
| Modality | Time-series mmWave radar point clouds |
| Recording unit | Complete participant–protocol–run recording |
| Collection protocols | Random walking, chair-sitting, bed/sofa-lying, and fall-and-recovery sequences |
| Frame-level classes | 10 activity and posture classes |
| Video release | Synchronized RGB video was used for annotation but is not distributed |

## Radar platform and setup

Data were acquired using the Texas Instruments (TI) **IWR6843ISK-ODS** antenna board with an **MMWAVEICBOOST** carrier board. The radar was mounted on a camera tripod at a height of approximately 1.5 m. Its boresight was perpendicular to the ground; no tilt angle was used.

The exact acquisition configuration is provided in `metadata/radar_configuration/<radar-configuration-file>.cfg`.

## Activity taxonomy

The release uses the following frame-level taxonomy. The raw labels in `frame_labels.csv` are mapped to these display names in `metadata/label_taxonomy.csv`.

| Class ID | Display name |
|---:|---|
| 0 | Standing/Walking |
| 1 | Falling |
| 2 | Floor-to-Stand |
| 3 | Stand-to-Sit |
| 4 | Sit-to-Lie |
| 5 | Lie-to-Sit |
| 6 | Sit-to-Stand |
| 7 | Sitting |
| 8 | Lying Down |
| 9 | Lying-on-Floor |

The four collection protocols are not the same as the frame-level classes:

- **walk:** approximately five minutes of random wandering with random turns and halts;
- **sit:** walk to a chair, sit down, remain seated briefly, stand up, and return; repeated approximately 50 times;
- **lie:** walk to a sofa or bed, lie down, remain lying briefly, get up, and return; repeated approximately 50 times; and
- **fall:** walk to the room center, fall, remain lying on the floor briefly, stand up, and return; repeated approximately 50 times.

For the sit and fall protocols, repetitions are approximately evenly distributed among front-facing, left-side-facing, and right-side-facing orientations relative to the sensor. For the lie protocol, repetitions are approximately evenly distributed between left-side-facing and right-side-facing orientations.

## Zenodo release layout

```text
mm-ADL-v1.0/
├── README.md
├── DATA_FORMAT.md
├── recordings/
│   └── sub-XX/protocol-<name>/run-YY/
│       ├── radar_data.csv
│       ├── frame_labels.csv
│       └── timestamps.csv
├── metadata/
│   ├── recording_manifest.csv
│   ├── protocol_definitions.csv
│   ├── label_taxonomy.csv
│   ├── file_schemas.csv
│   └── radar_configuration/
│       └── <radar-configuration-file>.cfg
└── scripts/
    └── align_camera_labels_to_radar.py
```

Each run contains a synchronized three-file unit:

- `radar_data.csv` contains radar point-cloud observations;
- `frame_labels.csv` contains activity labels in the camera-frame domain; and
- `timestamps.csv` maps camera frames to Unix timestamps.

See [DATA_FORMAT.md](DATA_FORMAT.md) for the exact file schemas and the camera-to-radar label-projection procedure.

## Generate labelled radar point clouds

The raw data are intentionally not distributed as fixed windows or directly labelled radar frames. To project camera-derived labels onto each radar run, run:

```bash
python scripts/align_camera_labels_to_radar.py --dataset-root /path/to/mm-ADL-v1.0
```

The script leaves `recordings/` unchanged and writes derived files to:

```text
derived/camera_to_radar_labels/sub-XX/protocol-<name>/run-YY/radar_data_labeled.csv
```

Use `--overwrite` to regenerate existing derived files. See `python scripts/align_camera_labels_to_radar.py --help` for options.

## Intended research uses

mm-ADL is intended for research on:

- mmWave radar human activity recognition;
- fall-related activity recognition;
- temporal segmentation and camera-to-radar annotation alignment;
- person identification and re-identification from radar point clouds; and
- representation learning for radar-based human sensing.

## Privacy and responsible use

Participant identifiers are pseudonymous, and the synchronized camera videos used for annotation are not released. An example RGB video illustrating the experimental protocol may be made available upon request to the corresponding author of the associated study. Nevertheless, radar point clouds can contain behavioral or biometric information. Users must follow the release license and applicable ethical, institutional, and legal requirements, and must not attempt to identify participants outside the scope of authorized research.

## Citation

The Zenodo DOI and recommended citation will be added here upon publication.

## License

The dataset license will be specified before public release.
