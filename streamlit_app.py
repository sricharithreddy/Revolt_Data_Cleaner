import os
import json
import base64
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_lottie import st_lottie

from Revoltv11 import process_file

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Revolt Motors",
    page_icon="⚡",
    layout="centered"
)

# =========================
# Helpers
# =========================
def get_base64_of_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_lottiefile(path: str):
    with open(path, "r") as f:
        return json.load(f)

# =========================
# Assets (Logo + Lottie)
# =========================
LOGO_PATH = "revolt_logo.png"
logo_html = ""
if os.path.exists(LOGO_PATH):
    logo_b64 = get_base64_of_file(LOGO_PATH)
    # Larger logo + subtle pulse animation (pure CSS)
    logo_html = (
        '<img src="data:image/png;base64,'
        + logo_b64
        + '" width="180" style="margin-right:15px; animation: pulse 2s infinite;">'
    )

bike_anim = None
if os.path.exists("bike.json"):
    try:
        bike_anim = load_lottiefile("bike.json")
    except Exception:
        bike_anim = None

# =========================
# Styling (CSS)
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3 { font-weight: 700 !important; }

/* Primary action button */
.stButton > button {
    background: linear-gradient(90deg, #e30613, #b0000d);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 0.6em 1.2em;
    font-size: 16px;
    font-weight: 600;
    transition: 0.3s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #b0000d, #7a0009);
    transform: scale(1.02);
}

/* Download buttons */
.stDownloadButton > button {
    border-radius: 8px;
    border: 1px solid #ddd;
    background-color: #fff;
    color: #333;
    font-weight: 500;
    padding: 0.5em 1em;
}
.stDownloadButton > button:hover {
    background-color: #f8f9fa;
    border-color: #e30613;
    color: #e30613;
}

/* Summary card */
.summary-card {
    padding: 20px;
    border-radius: 15px;
    background: #ffffff;
    border: 1px solid #eee;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    max-width: 650px;
    margin: 20px auto;
}

/* Logo pulse */
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================
header_html = (
    '<div style="display:flex; align-items:center; justify-content:center; margin-bottom:10px;">'
    + logo_html
    + '<h1 style="color:#222; margin:0;">Revolt Motors AI</h1>'
    + '</div>'
    + '<p style="text-align:center; color:#666; font-size:16px;">'
    + 'Upload raw Excel/CSV → get a <b>cleaned dataset</b>, <b>flagged log</b>, and an <b>updated blocklist</b>.'
    + '</p>'
    + '<hr style="margin:20px 0;">'
)
st.markdown(header_html, unsafe_allow_html=True)

# =========================
# Upload
# =========================
uploaded_file = st.file_uploader("📂 Upload your Excel/CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # Save upload to a temp file (preserve extension)
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    cleaned_output = "cleaned_output.xlsx"
    flagged_log = "flagged_log.txt"

    # Lottie animation above CTA
    if bike_anim:
        st.markdown("<h3 style='text-align:center;'>Ready to Clean?</h3>", unsafe_allow_html=True)
        st_lottie(bike_anim, speed=1, width=280, height=200, key="bike")

    # =========================
    # Run Cleaning
    # =========================
    if st.button("🏍️ Run Cleaning", use_container_width=True):
        result = process_file(input_path, cleaned_output, flagged_log)
        new_count = result.get("new_numbers", 0)

        # --- Stats ---
        # Cleaned totals
        cleaned_xl = pd.ExcelFile(cleaned_output)
        total_rows = sum(len(cleaned_xl.parse(s)) for s in cleaned_xl.sheet_names)

        # Original totals
        original_xl = pd.ExcelFile(input_path)
        orig_rows = sum(len(original_xl.parse(s)) for s in original_xl.sheet_names)

        removed_rows = orig_rows - total_rows

        # Blocklist size (new format Mobile Number, DateAdded)
        blocklist_size = 0
        if os.path.exists("seen_feedback_mobiles.csv"):
            try:
                seen_df = pd.read_csv("seen_feedback_mobiles.csv")
                blocklist_size = len(seen_df)
            except Exception:
                blocklist_size = 0

        # =========================
        # Summary
        # =========================
        st.markdown(
            (
                '<div class="summary-card">'
                '<h3 style="margin-top:0; color:#e30613;">📊 Process Summary</h3>'
                f'<p>✅ <b>Processed:</b> {orig_rows:,} rows</p>'
                f'<p>📤 <b>Cleaned File:</b> {total_rows:,} rows</p>'
                f'<p>🚫 <b>Removed (blocklisted):</b> {removed_rows:,} rows</p>'
                f'<p>📋 <b>Blocklist:</b> +{new_count:,} new (now total {blocklist_size:,})</p>'
                '</div>'
            ),
            unsafe_allow_html=True
        )

        # =========================
        # Downloads
        # =========================
        st.markdown("<h3 style='margin-top:30px;'>📥 Downloads</h3>", unsafe_allow_html=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.path.exists(cleaned_output):
            with open(cleaned_output, "rb") as f:
                st.download_button(
                    "⬇️ Download Cleaned File",
                    f,
                    file_name=f"cleaned_output_{ts}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        if os.path.exists(flagged_log):
            with open(flagged_log, "rb") as f:
                st.download_button(
                    "⬇️ Download Flagged Log",
                    f,
                    file_name=f"flagged_log_{ts}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        if os.path.exists("seen_feedback_mobiles.csv"):
            with open("seen_feedback_mobiles.csv", "rb") as f:
                st.download_button(
                    "⬇️ Download Blocklist",
                    f,
                    file_name=f"seen_feedback_mobiles_{ts}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
