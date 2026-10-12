"""
aiTransform: Image Format & Size Converter
Web Application powered by Streamlit and Pillow.
Supports JPG, PNG, and WebP conversion, resizing, and compression with live before/after metrics.
"""

import os
import io
import zipfile
from typing import Optional
import streamlit as st
from PIL import Image

from converter.image_processor import ImageProcessor

# Configure page
st.set_page_config(
    page_title="aiTransform — Image Format & Size Converter",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0284C7 100%);
        padding: 24px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.0rem;
        font-weight: 700;
        color: #FFFFFF !important;
    }
    .main-header p {
        margin: 6px 0 0 0;
        color: #94A3B8;
        font-size: 1.0rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.76rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 6px;
    }
    .badge-cyan { background-color: #E0F2FE; color: #0369A1; }
    .badge-emerald { background-color: #D1FAE5; color: #047857; }
    .badge-indigo { background-color: #EEF2FF; color: #4338CA; }
    .metric-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
    }
    .metric-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.78rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .savings-badge {
        font-size: 1.1rem;
        font-weight: 700;
        color: #16A34A;
    }
    .stDownloadButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_bytes(size_bytes: int) -> str:
    """Formats raw bytes into human readable KB or MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


# ------------------------------------------------------------------------------
# Sidebar: Input Selection & Conversion Options
# ------------------------------------------------------------------------------
st.sidebar.markdown("### 🖼️ aiTransform.com")
st.sidebar.caption("AI Tools & Transformation Products — Image Format & Size Converter")

input_mode = st.sidebar.radio(
    "Choose Input Source",
    ["📁 Upload Image(s)", "🧪 Test Sample Images"],
)

uploaded_files = []
active_bytes = None
original_name = "image"

if input_mode == "🧪 Test Sample Images":
    sample_options = {
        "Sample Photo (JPG - 1200x800)": "sample_images/sample_photo.jpg",
        "Transparent Badge (PNG - 600x600)": "sample_images/sample_badge.png",
        "Modern Graphic (WebP - 800x600)": "sample_images/sample_graphic.webp",
    }
    chosen_sample = st.sidebar.selectbox("Select Sample", list(sample_options.keys()))
    sample_path = sample_options[chosen_sample]
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            active_bytes = f.read()
        original_name = os.path.splitext(os.path.basename(sample_path))[0]
else:
    raw_uploads = st.sidebar.file_uploader(
        "Upload Image(s) (JPG, PNG, WebP)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Upload one or multiple images to convert, resize, and compress.",
    )
    if raw_uploads:
        uploaded_files = raw_uploads
        # Set primary active for single view
        active_bytes = uploaded_files[0].getvalue()
        original_name = os.path.splitext(uploaded_files[0].name)[0]

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Conversion Settings")

# Target format
target_format = st.sidebar.selectbox("Convert To Format", ["WEBP", "JPG", "PNG"], index=0)

# Resizing mode
resize_mode = st.sidebar.selectbox(
    "Resize Mode",
    ["Original Dimensions", "By Percentage (%)", "Custom Width & Height", "Standard Preset"],
)

target_width = None
target_height = None
scale_percentage = None
maintain_aspect = True

if resize_mode == "By Percentage (%)":
    scale_percentage = st.sidebar.slider("Scale Percentage", 10, 200, 50, step=5)

elif resize_mode == "Custom Width & Height":
    maintain_aspect = st.sidebar.checkbox("Maintain Aspect Ratio", value=True)
    c1, c2 = st.sidebar.columns(2)
    with c1:
        target_width = st.number_input("Width (px)", min_value=1, max_value=8000, value=800, step=50)
    with c2:
        target_height = st.number_input("Height (px)", min_value=1, max_value=8000, value=600, step=50)

elif resize_mode == "Standard Preset":
    presets = {
        "HD 1080p (1920 x 1080)": (1920, 1080),
        "Web Banner (1200 x 630)": (1200, 630),
        "Standard Web (800 x 600)": (800, 600),
        "Instagram Square (1080 x 1080)": (1080, 1080),
        "Thumbnail (250 x 250)": (250, 250),
        "Avatar Icon (100 x 100)": (100, 100),
    }
    chosen_preset = st.sidebar.selectbox("Select Preset", list(presets.keys()))
    target_width, target_height = presets[chosen_preset]
    maintain_aspect = True

# Compression & Quality Controls
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗜️ Compression & Quality")

quality = st.sidebar.slider(
    "Quality (Compression Level)",
    min_value=1,
    max_value=100,
    value=80,
    help="Lower values yield smaller file sizes with slight visual degradation.",
)

lossless_webp = False
if target_format == "WEBP":
    lossless_webp = st.sidebar.checkbox("Lossless WebP (Pixel-perfect)", value=False)

optimize_png = True
if target_format == "PNG":
    optimize_png = st.sidebar.checkbox("Optimize Palette & Deflate", value=True)


# ------------------------------------------------------------------------------
# Main Header
# ------------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>aiTransform: Image Format & Size Converter</h1>
        <p>Convert seamlessly between JPG, PNG, and WebP. Resize and compress images with instant before-and-after file size metrics.</p>
        <div style="margin-top: 10px;">
            <span class="badge-pill badge-cyan">✓ Convert JPG / PNG / WebP</span>
            <span class="badge-pill badge-emerald">✓ Before & After Size Analytics</span>
            <span class="badge-pill badge-indigo">✓ Aspect-Ratio Preserving Resize</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# Main Content
# ------------------------------------------------------------------------------
if active_bytes is None:
    st.info("👈 Please upload an image or choose one of the sample images from the sidebar to begin.")
else:
    # Multiple files check
    is_batch = len(uploaded_files) > 1

    if not is_batch:
        # SINGLE IMAGE VIEW
        with st.spinner("Processing image conversion and compression..."):
            result = ImageProcessor.process(
                input_bytes=active_bytes,
                target_format=target_format,
                target_width=target_width,
                target_height=target_height,
                percentage=scale_percentage,
                maintain_aspect_ratio=maintain_aspect,
                quality=quality,
                lossless_webp=lossless_webp,
                optimize=optimize_png,
            )

        orig_w, orig_h = result["original_dimensions"]
        new_w, new_h = result["output_dimensions"]
        orig_sz = result["original_size_bytes"]
        new_sz = result["output_size_bytes"]
        savings = result["savings_percent"]

        # Metric Cards Bar
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{format_bytes(orig_sz)}</div><div class="metric-lbl">Before Size</div></div>',
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{format_bytes(new_sz)}</div><div class="metric-lbl">After Size</div></div>',
                unsafe_allow_html=True,
            )
        with m3:
            sign = "-" if savings >= 0 else "+"
            color_class = "savings-badge" if savings >= 0 else "metric-val"
            st.markdown(
                f'<div class="metric-box"><div class="{color_class}">{sign}{abs(savings):.1f}%</div><div class="metric-lbl">Storage Saved</div></div>',
                unsafe_allow_html=True,
            )
        with m4:
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{orig_w}×{orig_h}</div><div class="metric-lbl">Original Res</div></div>',
                unsafe_allow_html=True,
            )
        with m5:
            st.markdown(
                f'<div class="metric-box"><div class="metric-val">{new_w}×{new_h}</div><div class="metric-lbl">New Res ({result["output_format"]})</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Side-by-Side Image Comparison
        col_before, col_after = st.columns(2, gap="large")

        with col_before:
            st.subheader("📷 Before (Original)")
            orig_pil = Image.open(io.BytesIO(active_bytes))
            st.image(orig_pil, caption=f"Original: {orig_w}×{orig_h}px ({format_bytes(orig_sz)})", use_container_width=True)

        with col_after:
            st.subheader(f"✨ After ({result['output_format']})")
            out_pil = Image.open(io.BytesIO(result["output_bytes"]))
            st.image(out_pil, caption=f"Converted: {new_w}×{new_h}px ({format_bytes(new_sz)})", use_container_width=True)

        # Download Section
        st.markdown("---")
        d_col1, d_col2 = st.columns([1, 2])
        with d_col1:
            download_filename = f"{original_name}_converted.{result['extension']}"
            st.download_button(
                label=f"📥 Download {result['output_format']} ({format_bytes(new_sz)})",
                data=result["output_bytes"],
                file_name=download_filename,
                mime=result["mime_type"],
                use_container_width=True,
            )
        with d_col2:
            st.caption(f"Ready for download. Compression saved {format_bytes(abs(result['size_diff_bytes']))} ({savings:+.1f}%).")

    else:
        # BATCH PROCESSING VIEW
        st.subheader(f"📦 Batch Processing ({len(uploaded_files)} Images)")
        st.markdown("Convert and compress all uploaded images with the selected settings.")

        batch_results = []
        progress_bar = st.progress(0)

        for idx, f in enumerate(uploaded_files):
            file_bytes = f.getvalue()
            name_root = os.path.splitext(f.name)[0]
            res = ImageProcessor.process(
                input_bytes=file_bytes,
                target_format=target_format,
                target_width=target_width,
                target_height=target_height,
                percentage=scale_percentage,
                maintain_aspect_ratio=maintain_aspect,
                quality=quality,
                lossless_webp=lossless_webp,
                optimize=optimize_png,
            )
            batch_results.append((name_root, res))
            progress_bar.progress((idx + 1) / len(uploaded_files))

        total_orig = sum(r["original_size_bytes"] for _, r in batch_results)
        total_new = sum(r["output_size_bytes"] for _, r in batch_results)
        total_savings = round(((total_orig - total_new) / total_orig) * 100.0, 2) if total_orig > 0 else 0.0

        bm1, bm2, bm3 = st.columns(3)
        bm1.metric("Total Before Size", format_bytes(total_orig))
        bm2.metric("Total After Size", format_bytes(total_new))
        bm3.metric("Total Space Saved", f"{total_savings:.1f}%", delta=f"{format_bytes(total_orig - total_new)}")

        # Create ZIP archive for 1-click batch download
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name_root, r in batch_results:
                zip_file.writestr(f"{name_root}_converted.{r['extension']}", r["output_bytes"])
        zip_bytes = zip_buf.getvalue()

        st.download_button(
            label=f"📥 Download All as ZIP ({format_bytes(len(zip_bytes))})",
            data=zip_bytes,
            file_name="aiTransform_converted_images.zip",
            mime="application/zip",
            use_container_width=True,
        )

        # Batch summary table
        st.markdown("#### 📋 Processed Files Breakdown")
        table_data = []
        for name_root, r in batch_results:
            table_data.append({
                "Filename": f"{name_root}.{r['extension']}",
                "Original Size": format_bytes(r["original_size_bytes"]),
                "New Size": format_bytes(r["output_size_bytes"]),
                "Savings": f"{r['savings_percent']:+.1f}%",
                "New Dimensions": f"{r['output_dimensions'][0]}×{r['output_dimensions'][1]}",
            })
        st.dataframe(table_data, use_container_width=True)
