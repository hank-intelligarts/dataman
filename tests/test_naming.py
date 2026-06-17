import pytest
from dataman.naming import validate_name, validate_version, dataset_dir_name, snapshot_tag


def test_validate_name_accepts_lowercase_alphanumeric_underscore():
    assert validate_name("pedestrian") is None


def test_validate_name_rejects_spaces():
    with pytest.raises(ValueError, match="lowercase alphanumeric"):
        validate_name("my dataset")


def test_validate_name_rejects_uppercase():
    with pytest.raises(ValueError, match="lowercase alphanumeric"):
        validate_name("Pedestrian")


def test_validate_version_accepts_major_minor():
    assert validate_version("2.0") is None


def test_validate_version_rejects_vprefix():
    with pytest.raises(ValueError, match="numeric"):
        validate_version("v2.0")


def test_validate_version_rejects_text():
    with pytest.raises(ValueError, match="numeric"):
        validate_version("two")


def test_dataset_dir_name():
    assert dataset_dir_name("pedestrian", "2.0", "20260601") == "pedestrian_v2.0_20260601"


def test_snapshot_tag():
    assert snapshot_tag("pedestrian", "2.0") == "dataset/pedestrian/v2.0"
