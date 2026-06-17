import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import cv2
from PIL import Image, UnidentifiedImageError

from dataman.config import ALLOWED_EXTENSIONS, MIN_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass
class QualityIssue:
    kind: str  # corrupt | duplicate | resolution_anomaly | unsupported_format
    file: str
    detail: str = ""


@dataclass
class ScanResult:
    file_count: int
    total_size_bytes: int
    issues: List[QualityIssue]
    quality_score: float


def scan_dataset(dataset_path: Path) -> ScanResult:
    data_dir = dataset_path
    all_files = [f for f in data_dir.rglob("*") if f.is_file() and f.name not in {"metadata.json", "manifest.txt"}]
    issues: List[QualityIssue] = []
    seen_hashes: dict[str, str] = {}
    total_size = sum(f.stat().st_size for f in all_files)

    for f in all_files:
        ext = f.suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            issues.append(QualityIssue(kind="unsupported_format", file=f.name,
                                       detail=f"extension {ext!r} not allowed"))
            continue

        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if digest in seen_hashes:
            issues.append(QualityIssue(kind="duplicate", file=f.name,
                                       detail=f"same content as {seen_hashes[digest]}"))
        else:
            seen_hashes[digest] = f.name

        if ext in IMAGE_EXTENSIONS:
            _check_image(f, issues)
        elif ext in VIDEO_EXTENSIONS:
            _check_video(f, issues)

    bad_count = len({i.file for i in issues})
    quality_score = round((1 - bad_count / max(len(all_files), 1)) * 100, 2) if all_files else 100.0
    return ScanResult(
        file_count=len(all_files),
        total_size_bytes=total_size,
        issues=issues,
        quality_score=quality_score,
    )


def _check_image(f: Path, issues: List[QualityIssue]) -> None:
    try:
        with Image.open(f) as img:
            img.verify()
        with Image.open(f) as img:
            w, h = img.size
            if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
                issues.append(QualityIssue(kind="resolution_anomaly", file=f.name,
                                           detail=f"{w}x{h} below minimum {MIN_IMAGE_DIMENSION}px"))
            elif w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
                issues.append(QualityIssue(kind="resolution_anomaly", file=f.name,
                                           detail=f"{w}x{h} above maximum {MAX_IMAGE_DIMENSION}px"))
    except (UnidentifiedImageError, Exception):
        issues.append(QualityIssue(kind="corrupt", file=f.name, detail="PIL could not open image"))


def _check_video(f: Path, issues: List[QualityIssue]) -> None:
    cap = cv2.VideoCapture(str(f))
    if not cap.isOpened():
        issues.append(QualityIssue(kind="corrupt", file=f.name, detail="cv2 could not open video"))
        return
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
        issues.append(QualityIssue(kind="resolution_anomaly", file=f.name,
                                   detail=f"{w}x{h} below minimum {MIN_IMAGE_DIMENSION}px"))
