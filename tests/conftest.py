import pytest
from pathlib import Path
from PIL import Image


@pytest.fixture
def tmp_dataset(tmp_path):
    d = tmp_path / "pedestrian_v2_20260601"
    d.mkdir(parents=True)
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img.save(d / "frame_0001.jpg")
    return d
