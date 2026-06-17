# AI Training Data Management Pipeline — Design Spec

## Context

A small team (< 10) of data scientists runs AI training on self-built on-prem GPU servers.
Training data (images/video) is currently scattered across different machines with no unified
management. The goal is to establish:

1. **Dataset versioning + tagging** — every dataset has a version and a unique snapshot ID
2. **Naming conventions** — standardized folder/file naming across all machines
3. **Reproducibility** — someone can reference a snapshot ID and use the exact same data
4. **Quality monitoring** — automatic scanning for bad files, duplicates, resolution anomalies
5. **Web UI** — browser-based dashboard to browse, search, and compare dataset versions

Not required: training code integration, experiment tracking, hyperparameter logging.

---

## Architecture

```
GPU Server 1, 2, 3...              NFS Mount (/mnt/shared_data)
local staging data     →  dvc push →  /mnt/shared_data/dvc-remote/  (hash cache)
                                              ↑
                                   dvc pull ← training job on each GPU server
                                   (data downloaded to local machine before training)

                                   /mnt/shared_data/datasets/  (human-readable, optional)
                                   ← registered datasets with metadata.json

                                   Central bare Git repo (on NFS or Gitea)
                                   ← DVC .dvc files + Git tags
                                              ↑
                                   Web Service (shared server)
                                   reads Git repo → Web UI
```

### NFS Directory Layout

```
/mnt/shared_data/
  dvc-remote/          ← DVC content-addressed cache (hash directory structure)
    ab/
      cdef1234...      ← actual files named by hash
    12/
      3456abcd...
  datasets/            ← human-readable registered dataset directories
    pedestrian_v2_20260601/
      metadata.json
      manifest.txt
      data/
```

### Four Components

#### 1. NFS as Shared Storage (existing infrastructure)
- All GPU servers mount `/mnt/shared_data`
- DVC remote points to `/mnt/shared_data/dvc-remote/` (hash cache format)
- Training jobs run `dvc pull` to download data to local machine before training
- Human-readable dataset directories under `/mnt/shared_data/datasets/` for reference

#### 2. DVC + Git (versioning + tagging)
- DVC tracks dataset files via checksums (stored in `.dvc` files in Git)
- Git tags mark dataset versions: `dataset/{name}/v{version}`
- Each tag = reproducible snapshot ID
- Central bare Git repo shared by all scientists (hosted on NFS or Gitea)
- All scientists push/pull from the same Git remote to stay in sync

**Naming convention** (enforced at registration time):
```
/mnt/shared_data/datasets/{name}_{version}_{YYYYMMDD}/
  ├── metadata.json     ← auto-generated: file count, size, quality score
  ├── manifest.txt      ← checksums of all files
  └── data/
        └── *.mp4 / *.jpg / ...
```

**Registration flow:**
```bash
dataman register --path /path/to/local/pedestrian_v2_20260601 \
                 --name pedestrian --version 2.0
# Runs: dvc add → dvc push → git commit → git tag → git push
# Output: Snapshot ID → dataset/pedestrian/v2.0
```

**Reproducibility flow:**
```bash
dataman info dataset/pedestrian/v2.0
# → path: /mnt/shared_data/datasets/pedestrian_v2_20260601
# → files: 12,450  size: 234.5GB  quality: 98.2%
# → registered by: austin  on: 2026-06-01

dataman pull dataset/pedestrian/v2.0
# → git checkout dataset/pedestrian/v2.0 → dvc pull
# → data downloaded to local machine
```

#### 3. `dataman` Python CLI
Thin wrapper around DVC + Git. Installed on all machines via pip.

Commands: `register`, `info`, `list`, `scan`, `verify`

Quality checks at register time:
- Corrupt/unreadable files
- Resolution out of expected range
- Duplicate files (hash comparison)
- Missing or malformed metadata
- File format validation (mp4, avi, mov, jpg, png)

#### 4. Web UI (FastAPI + lightweight frontend)
Hosted on shared server. Reads Git repo metadata — no separate database.
No write operations from the UI — all writes go through `dataman` CLI.

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Data versioning | DVC |
| Version history | Git (tags = snapshot IDs) |
| Quality scanning | Custom Python (cv2, PIL) |
| CLI wrapper | Python + Click |
| Web backend | FastAPI + gitpython |
| Web frontend | Plain HTML/JS |
| Shared storage | NFS (existing) |
