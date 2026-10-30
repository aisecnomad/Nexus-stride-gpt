"""Untrusted uploads are bounded and rejected before any provider traffic."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from apps.web.uploads import read_diagram_image


def _image(fmt="PNG", size=(2, 2)):
    stream = io.BytesIO()
    Image.new("RGB", size, "red").save(stream, format=fmt)
    return stream


@pytest.mark.parametrize("fmt,media_type", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_media_type_comes_from_verified_content_and_position_survives(fmt, media_type):
    upload = _image(fmt)
    upload.type = "application/javascript"
    upload.seek(3)
    original = upload.getvalue()
    assert read_diagram_image(upload) == (original, media_type)
    assert upload.tell() == 3
    assert read_diagram_image(upload) == (original, media_type)


@pytest.mark.parametrize("data", [b"", b"not an image", b"\x89PNG\r\n\x1a\n"])
def test_empty_forged_and_truncated_image_headers_are_rejected(data):
    with pytest.raises(ValueError):
        read_diagram_image(io.BytesIO(data))


def test_corrupt_png_structure_is_rejected():
    with pytest.raises(ValueError):
        read_diagram_image(io.BytesIO(_image().getvalue()[:-10]))


def test_non_png_jpeg_image_is_rejected():
    with pytest.raises(ValueError, match="Only PNG and JPEG"):
        read_diagram_image(_image("GIF"))


def test_upload_read_stops_at_byte_budget(monkeypatch):
    import apps.web.uploads as uploads

    class BoundedRead(io.BytesIO):
        def read(self, size=-1):
            assert size == 17
            return super().read(size)

    monkeypatch.setattr(uploads, "MAX_IMAGE_BYTES", 16)
    with pytest.raises(ValueError, match="10 MiB"):
        read_diagram_image(BoundedRead(b"x" * 100))


def test_decoded_pixel_budget_rejects_small_compressed_large_image(monkeypatch):
    monkeypatch.setattr("apps.web.uploads.MAX_IMAGE_PIXELS", 3)
    with pytest.raises(ValueError, match="million pixels"):
        read_diagram_image(_image(size=(2, 2)))
