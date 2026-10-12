# 🖼️ aiTransform: Image Format & Size Converter

> **aiTransform.com** — *AI tools and transformation content/products.*  
> **Source:** Zeshan Request ZR-26-00755 (*TechAbout_Additional_Tasks_Sheet_v2*, prepared by Hassan Haque, 8 Oct 2026)  
> **Role:** AI / ML Engineer | Task 1 of 20 (Easy)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Pillow](https://img.shields.io/badge/Pillow-10.0%2B-brightgreen.svg)](https://python-pillow.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-12%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🌟 Overview & What It Does

**aiTransform Image Format & Size Converter** is a lightweight, responsive utility designed to convert, resize, and compress images with real-time before-and-after storage analytics.

### Key Capabilities:
1. **Format Conversion:** Seamless bidirectional conversion between **JPG**, **PNG**, and **WebP**. Handles alpha-channel transparency safely when converting from RGBA (PNG/WebP) to JPEG by compositing onto a clean solid background.
2. **Dimension Resizing:**
   - **Proportional Scaling:** Maintains original aspect ratio automatically.
   - **Percentage Scaling:** Quick slider (10% to 200%).
   - **Standard Presets:** HD 1080p, Web Banner (1200x630), Standard Web (800x600), Instagram Square (1080x1080), Thumbnail (250x250), and Avatar (100x100).
3. **Compression & File Size Analytics:**
   - Real-time **Before vs After file size** comparison (KB / MB).
   - Exact storage savings percentage calculated (`-X% saved`).
   - Granular quality control (1-100) with WebP lossless option and PNG optimization.
4. **Batch Conversion:** Upload multiple images simultaneously, view aggregated space savings, and download all converted files as a single ZIP archive.

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- `git`

### 2. Clone Repository
```bash
git clone https://github.com/tayyabshahid029021/aitransform-image-converter.git
cd aitransform-image-converter
```

### 3. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

---

## 🧪 How It Was Tested (12 Automated Tests)

The core conversion engine (`converter/image_processor.py`) is validated using an automated `pytest` test suite:

```bash
python3 -m pytest tests/ -v
```

### Test Suite Breakdown:
1. `test_jpg_to_png_conversion` — Verifies valid PNG output structure and MIME type.
2. `test_png_to_webp_conversion` — Verifies lossy WebP compression and encoding.
3. `test_webp_to_jpg_conversion` — Verifies WebP decoding to standard JPEG.
4. `test_transparency_rgba_to_jpg` — Verifies transparency flattening without `OSError`.
5. `test_resize_by_dimensions_maintain_aspect_ratio` — Verifies mathematical bounding-box aspect ratio calculation (e.g. 1000x500 to 500x250).
6. `test_resize_by_dimensions_exact` — Verifies exact pixel dimensions when aspect ratio locking is disabled.
7. `test_resize_by_percentage` — Verifies 50% scaling halves width and height cleanly.
8. `test_compression_quality_reduces_file_size` — Verifies lower quality slider yields strictly smaller file sizes.
9. `test_webp_compression_efficiency` — Verifies input and output byte accounting.
10. `test_webp_lossless_mode` — Verifies lossless WebP pixel retention.
11. `test_invalid_format_raises_error` — Validates error handling on unsupported formats.
12. `test_mime_type_and_extension_mapping` — Validates HTTP download MIME types.

---

## ⚠️ Limitations

1. **Supported Formats:** Focused specifically on web image standards (**JPG, PNG, WebP**). Multi-page TIFF, camera RAW formats, and animated GIF/APNG sequence frames are not supported in this version.
2. **Extreme Compression Artifacts:** Quality settings below 20 may produce 8x8 block discrete cosine transform (DCT) artifacts in JPEGs or edge blurring in WebP.
3. **Very Large Files (> 50MB):** Ultra-high-resolution images (8K+) require sufficient memory for Lanczos resampling.

---

## 👨‍💻 Submission Details

- **Client / Platform:** aiTransform.com
- **Author:** Tayyab Shahid (AI/ML Engineer)
- **Email:** `tayyabshahid029021@gmail.com`
- **Request ID:** Zeshan Request ZR-26-00755 (*TechAbout_Additional_Tasks_Sheet_v2*, Task 1 of 20 - Easy)
- **Lead / Evaluator:** Hassan Haque (Prepared 8 Oct 2026)
- **Live Demo URL:** [https://aitransform-image-converter.streamlit.app](https://aitransform-image-converter.streamlit.app)
- **GitHub Repository:** [https://github.com/tayyabshahid029021/aitransform-image-converter](https://github.com/tayyabshahid029021/aitransform-image-converter)
