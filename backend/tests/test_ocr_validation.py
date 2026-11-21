import io

import pytest
from PIL import Image

from backend.app.services.ocr_service import validate_image_bytes


def make_png(size=(8, 8)):
    image = Image.new("RGB", size, color="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_accepts_valid_png_and_reports_real_dimensions():
    mime, width, height = validate_image_bytes(make_png((13, 7)))

    assert (mime, width, height) == ("image/png", 13, 7)


def test_rejects_non_image_bytes_even_with_png_extension():
    with pytest.raises(ValueError, match="Invalid image"):
        validate_image_bytes(b"this is not a png")


def test_rejects_image_over_byte_limit():
    with pytest.raises(ValueError, match="byte size"):
        validate_image_bytes(make_png(), max_bytes=10)


def test_rejects_image_over_pixel_limit():
    with pytest.raises(ValueError, match="pixel limit"):
        validate_image_bytes(make_png((20, 20)), max_pixels=100)


def test_rejects_unsupported_image_format():
    image = Image.new("RGB", (5, 5), color="white")
    output = io.BytesIO()
    image.save(output, format="GIF")

    with pytest.raises(ValueError, match="PNG and JPEG"):
        validate_image_bytes(output.getvalue())
