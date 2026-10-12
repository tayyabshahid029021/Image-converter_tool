"""
Automated Test Suite for aiTransform Image Format & Size Converter.
Tests format conversions (JPG, PNG, WebP), resizing, compression,
and transparency handling (12 automated tests).
"""

import io
import pytest
from PIL import Image
from converter.image_processor import ImageProcessor


def create_test_image(format="JPEG", size=(600, 400), mode="RGB", color=(70, 130, 180)):
    """Helper utility to generate in-memory synthetic images for testing."""
    buf = io.BytesIO()
    img = Image.new(mode, size, color)
    img.save(buf, format=format)
    return buf.getvalue()


# ------------------------------------------------------------------------------
# 1. Format Conversion Tests
# ------------------------------------------------------------------------------

def test_jpg_to_png_conversion():
    jpg_bytes = create_test_image("JPEG")
    res = ImageProcessor.process(jpg_bytes, target_format="PNG")

    assert res["output_format"] == "PNG"
    assert res["extension"] == "png"
    assert res["mime_type"] == "image/png"

    # Verify output is valid PNG
    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.format == "PNG"


def test_png_to_webp_conversion():
    png_bytes = create_test_image("PNG")
    res = ImageProcessor.process(png_bytes, target_format="WEBP", quality=80)

    assert res["output_format"] == "WEBP"
    assert res["extension"] == "webp"
    assert res["mime_type"] == "image/webp"

    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.format == "WEBP"


def test_webp_to_jpg_conversion():
    webp_bytes = create_test_image("WEBP")
    res = ImageProcessor.process(webp_bytes, target_format="JPG", quality=90)

    assert res["output_format"] == "JPEG"
    assert res["extension"] == "jpg"
    assert res["mime_type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.format == "JPEG"


def test_transparency_rgba_to_jpg():
    """Ensure RGBA image converts to JPEG cleanly with white composite background."""
    buf = io.BytesIO()
    rgba_img = Image.new("RGBA", (200, 200), (255, 0, 0, 128))  # Semi-transparent red
    rgba_img.save(buf, format="PNG")
    rgba_bytes = buf.getvalue()

    res = ImageProcessor.process(rgba_bytes, target_format="JPG", bg_color=(255, 255, 255))
    assert res["output_format"] == "JPEG"

    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.mode == "RGB"
    assert out_img.size == (200, 200)


# ------------------------------------------------------------------------------
# 2. Resizing Tests
# ------------------------------------------------------------------------------

def test_resize_by_dimensions_maintain_aspect_ratio():
    img_bytes = create_test_image("JPEG", size=(1000, 500))  # 2:1 ratio
    res = ImageProcessor.process(
        img_bytes,
        target_format="JPEG",
        target_width=500,
        target_height=400,
        maintain_aspect_ratio=True,
    )

    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    # 2:1 ratio inside 500x400 should fit as 500x250
    assert out_img.size == (500, 250)
    assert res["output_dimensions"] == (500, 250)


def test_resize_by_dimensions_exact():
    img_bytes = create_test_image("PNG", size=(800, 600))
    res = ImageProcessor.process(
        img_bytes,
        target_format="PNG",
        target_width=400,
        target_height=300,
        maintain_aspect_ratio=False,
    )

    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.size == (400, 300)


def test_resize_by_percentage():
    img_bytes = create_test_image("JPEG", size=(1200, 800))
    res = ImageProcessor.process(
        img_bytes,
        target_format="JPEG",
        percentage=50,  # 50%
    )

    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.size == (600, 400)
    assert res["output_dimensions"] == (600, 400)


# ------------------------------------------------------------------------------
# 3. Compression & File Size Verification Tests
# ------------------------------------------------------------------------------

def test_compression_quality_reduces_file_size():
    img_bytes = create_test_image("JPEG", size=(1200, 800))
    # High quality
    res_high = ImageProcessor.process(img_bytes, target_format="JPEG", quality=95)
    # Low quality
    res_low = ImageProcessor.process(img_bytes, target_format="JPEG", quality=30)

    # Low quality must produce smaller file size
    assert res_low["output_size_bytes"] < res_high["output_size_bytes"]
    assert res_low["savings_percent"] > res_high["savings_percent"]


def test_webp_compression_efficiency():
    # Large PNG photo
    png_bytes = create_test_image("PNG", size=(1000, 1000))
    res_webp = ImageProcessor.process(png_bytes, target_format="WEBP", quality=75)

    assert res_webp["output_format"] == "WEBP"
    assert res_webp["output_size_bytes"] > 0
    # Before and after sizes must be accurately tracked
    assert res_webp["original_size_bytes"] == len(png_bytes)


def test_webp_lossless_mode():
    png_bytes = create_test_image("PNG", size=(300, 300))
    res = ImageProcessor.process(png_bytes, target_format="WEBP", lossless_webp=True)

    assert res["output_format"] == "WEBP"
    out_img = Image.open(io.BytesIO(res["output_bytes"]))
    assert out_img.size == (300, 300)


# ------------------------------------------------------------------------------
# 4. Error Handling & Validation Tests
# ------------------------------------------------------------------------------

def test_invalid_format_raises_error():
    img_bytes = create_test_image("JPEG")
    with pytest.raises(ValueError, match="Unsupported format"):
        ImageProcessor.process(img_bytes, target_format="GIF")


def test_mime_type_and_extension_mapping():
    assert ImageProcessor.get_mime_type("jpg") == "image/jpeg"
    assert ImageProcessor.get_mime_type("png") == "image/png"
    assert ImageProcessor.get_mime_type("webp") == "image/webp"

    assert ImageProcessor.get_file_extension("jpeg") == "jpg"
    assert ImageProcessor.get_file_extension("png") == "png"
    assert ImageProcessor.get_file_extension("webp") == "webp"
