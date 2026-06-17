import pytest
from pathlib import Path
from PIL import Image
from dataman.scanner import scan_dataset, ScanResult, QualityIssue


def _make_jpg(path: Path, w: int, h: int) -> None:
    Image.new("RGB", (w, h), color=(128, 64, 32)).save(path)


def test_clean_dataset_has_no_issues(tmp_path):
    _make_jpg(tmp_path / "a.jpg", 640, 480)
    _make_jpg(tmp_path / "b.jpg", 320, 240)
    result = scan_dataset(tmp_path)
    assert isinstance(result, ScanResult)
    assert result.issues == []
    assert result.file_count == 2
    assert result.quality_score == 100.0


def test_detects_corrupt_file(tmp_path):
    (tmp_path / "bad.jpg").write_bytes(b"\xff\xd8\xff corrupt garbage")
    result = scan_dataset(tmp_path)
    issues = [i for i in result.issues if i.kind == "corrupt"]
    assert len(issues) == 1
    assert "bad.jpg" in issues[0].file


def test_detects_unsupported_format(tmp_path):
    (tmp_path / "notes.txt").write_text("hello")
    result = scan_dataset(tmp_path)
    issues = [i for i in result.issues if i.kind == "unsupported_format"]
    assert len(issues) == 1


def test_detects_duplicate_files(tmp_path):
    content = b"identical bytes" * 100
    (tmp_path / "a.jpg").write_bytes(content)
    (tmp_path / "b.jpg").write_bytes(content)
    result = scan_dataset(tmp_path)
    issues = [i for i in result.issues if i.kind == "duplicate"]
    assert len(issues) >= 1


def test_detects_resolution_anomaly(tmp_path):
    _make_jpg(tmp_path / "tiny.jpg", 4, 4)
    result = scan_dataset(tmp_path)
    issues = [i for i in result.issues if i.kind == "resolution_anomaly"]
    assert len(issues) == 1


def test_quality_score_decreases_with_issues(tmp_path):
    _make_jpg(tmp_path / "ok.jpg", 640, 480)
    (tmp_path / "bad.jpg").write_bytes(b"junk")
    result = scan_dataset(tmp_path)
    assert result.quality_score < 100.0
