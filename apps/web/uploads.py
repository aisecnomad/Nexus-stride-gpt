"""Bound untrusted diagram images before decoding or sending them to a provider."""

from __future__ import annotations

import io
import warnings
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000


def read_diagram_image(upload: BinaryIO) -> tuple[bytes, str]:
    """Read a bounded PNG/JPEG, verify its structure, and derive its media type.

    The client filename and MIME type are untrusted. Never decode pixels here;
    a byte cap and explicit dimension cap bound both compressed and decoded size.
    Restore the stream position so Streamlit reruns and retries see the same data.
    """
    position = upload.tell()
    try:
        upload.seek(0)
        data = upload.read(MAX_IMAGE_BYTES + 1)
    finally:
        upload.seek(position)
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Upload a nonempty PNG or JPEG image no larger than 10 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {"PNG", "JPEG"}:
                    raise ValueError("Only PNG and JPEG diagram images are supported.")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Diagram images must contain no more than 16 million pixels.")
                media_type = "image/png" if image.format == "PNG" else "image/jpeg"
                image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError,
            Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError("The upload is not a valid PNG or JPEG image.") from exc
    return data, media_type
