"""
Core Image Conversion, Resizing, and Compression Engine.
Supports JPG, PNG, and WebP with high-quality resampling, transparency handling,
and file size optimization.
"""

import io
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageOps


class ImageProcessor:
    """Provides modular image conversion, resizing, and compression routines."""

    SUPPORTED_FORMATS = ["JPG", "JPEG", "PNG", "WEBP"]

    @classmethod
    def normalize_format(cls, fmt: str) -> str:
        """Normalizes format string to standard PIL format name."""
        fmt_upper = fmt.strip().upper()
        if fmt_upper in ["JPG", "JPEG"]:
            return "JPEG"
        if fmt_upper == "PNG":
            return "PNG"
        if fmt_upper in ["WEBP", "WEB_P"]:
            return "WEBP"
        raise ValueError(f"Unsupported format '{fmt}'. Supported formats: JPG, PNG, WebP")

    @classmethod
    def get_mime_type(cls, fmt: str) -> str:
        """Returns standard MIME type for format."""
        norm = cls.normalize_format(fmt)
        if norm == "JPEG":
            return "image/jpeg"
        if norm == "PNG":
            return "image/png"
        if norm == "WEBP":
            return "image/webp"
        return "application/octet-stream"

    @classmethod
    def get_file_extension(cls, fmt: str) -> str:
        """Returns standard lowercase file extension."""
        norm = cls.normalize_format(fmt)
        if norm == "JPEG":
            return "jpg"
        if norm == "PNG":
            return "png"
        if norm == "WEBP":
            return "webp"
        return "bin"

    @classmethod
    def prepare_for_format(
        cls,
        image: Image.Image,
        target_format: str,
        bg_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Prepares image mode for target format.
        Handles transparency conversion when converting to JPEG.
        """
        norm_fmt = cls.normalize_format(target_format)

        if norm_fmt == "JPEG":
            # JPEG does not support transparency
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                # Convert palette to RGBA first
                rgba_img = image.convert("RGBA")
                background = Image.new("RGB", rgba_img.size, bg_color)
                background.paste(rgba_img, mask=rgba_img.split()[3])
                return background
            elif image.mode != "RGB":
                return image.convert("RGB")
            return image

        elif norm_fmt in ("PNG", "WEBP"):
            # PNG and WebP support RGB, RGBA, and Grayscale (L)
            if image.mode not in ("RGB", "RGBA", "L"):
                return image.convert("RGBA" if "transparency" in image.info else "RGB")
            return image

        return image

    @classmethod
    def resize_image(
        cls,
        image: Image.Image,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        percentage: Optional[float] = None,
        maintain_aspect_ratio: bool = True,
    ) -> Image.Image:
        """
        Resizes an image using high-quality Lanczos resampling.
        
        Args:
            image: PIL Image instance
            target_width: Explicit new width in pixels
            target_height: Explicit new height in pixels
            percentage: Scaling percentage (e.g. 50 for 50%)
            maintain_aspect_ratio: Keep proportional dimensions
        """
        orig_w, orig_h = image.size

        # Resizing by percentage
        if percentage is not None and percentage > 0:
            scale = percentage / 100.0
            new_w = max(1, int(round(orig_w * scale)))
            new_h = max(1, int(round(orig_h * scale)))
            return image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Resizing by target dimensions
        if target_width is not None or target_height is not None:
            if maintain_aspect_ratio:
                if target_width is not None and target_height is not None:
                    # Fit within the bounding box preserving aspect ratio
                    ratio = min(target_width / orig_w, target_height / orig_h)
                    new_w = max(1, int(round(orig_w * ratio)))
                    new_h = max(1, int(round(orig_h * ratio)))
                elif target_width is not None:
                    ratio = target_width / orig_w
                    new_w = max(1, target_width)
                    new_h = max(1, int(round(orig_h * ratio)))
                else:
                    ratio = target_height / orig_h
                    new_w = max(1, int(round(orig_w * ratio)))
                    new_h = max(1, target_height)
            else:
                new_w = target_width if target_width is not None else orig_w
                new_h = target_height if target_height is not None else orig_h

            if (new_w, new_h) != (orig_w, orig_h):
                return image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        return image

    @classmethod
    def process(
        cls,
        input_bytes: bytes,
        target_format: str,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        percentage: Optional[float] = None,
        maintain_aspect_ratio: bool = True,
        quality: int = 85,
        lossless_webp: bool = False,
        optimize: bool = True,
        bg_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Dict[str, Any]:
        """
        Comprehensive pipeline: reads, resizes, converts, and compresses.
        
        Returns dictionary containing:
            - output_bytes: result image binary data
            - original_size_bytes: input size in bytes
            - output_size_bytes: compressed size in bytes
            - original_dimensions: (orig_w, orig_h)
            - output_dimensions: (new_w, new_h)
            - original_format: e.g. 'JPEG'
            - output_format: e.g. 'WEBP'
            - size_diff_bytes: size difference
            - savings_percent: percentage reduced (positive is smaller)
            - mime_type: output MIME type
            - extension: output file extension
        """
        # Validate format
        norm_fmt = cls.normalize_format(target_format)
        orig_size = len(input_bytes)

        # Open image
        img = Image.open(io.BytesIO(input_bytes))
        # Auto-orient based on EXIF tag if present
        img = ImageOps.exif_transpose(img) or img

        orig_w, orig_h = img.size
        orig_format = img.format or "UNKNOWN"

        # 1. Resize
        resized_img = cls.resize_image(
            img,
            target_width=target_width,
            target_height=target_height,
            percentage=percentage,
            maintain_aspect_ratio=maintain_aspect_ratio,
        )
        new_w, new_h = resized_img.size

        # 2. Mode & Transparency Preparation
        prepared_img = cls.prepare_for_format(resized_img, norm_fmt, bg_color=bg_color)

        # 3. Save & Compress
        output_buffer = io.BytesIO()
        save_kwargs = {}

        if norm_fmt == "JPEG":
            save_kwargs["quality"] = max(1, min(100, int(quality)))
            save_kwargs["optimize"] = optimize
            save_kwargs["progressive"] = True
        elif norm_fmt == "WEBP":
            save_kwargs["quality"] = max(1, min(100, int(quality)))
            save_kwargs["lossless"] = lossless_webp
            save_kwargs["method"] = 6  # highest compression effort
        elif norm_fmt == "PNG":
            save_kwargs["optimize"] = optimize
            # PNG compression level (0-9) mapped from quality
            # High quality = standard max compression (9)
            save_kwargs["compress_level"] = 9 if optimize else 6

        prepared_img.save(output_buffer, format=norm_fmt, **save_kwargs)
        output_bytes = output_buffer.getvalue()
        new_size = len(output_bytes)

        # Compression calculation
        size_diff = orig_size - new_size
        savings_percent = round(((orig_size - new_size) / orig_size) * 100.0, 2) if orig_size > 0 else 0.0

        return {
            "output_bytes": output_bytes,
            "original_size_bytes": orig_size,
            "output_size_bytes": new_size,
            "original_dimensions": (orig_w, orig_h),
            "output_dimensions": (new_w, new_h),
            "original_format": orig_format,
            "output_format": norm_fmt,
            "size_diff_bytes": size_diff,
            "savings_percent": savings_percent,
            "mime_type": cls.get_mime_type(norm_fmt),
            "extension": cls.get_file_extension(norm_fmt),
        }
