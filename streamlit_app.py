import streamlit as st
import os
import tempfile
import pandas as pd
from datetime import datetime
from Revoltv11 import process_file

# ------------------------
# Page Config
# ------------------------
st.set_page_config(
    page_title="Revolt Data Cleaner",
    page_icon="⚡",
    layout="centered"
)

# ------------------------
# Custom CSS Styling
# ------------------------
st.markdown("""
    <style>
    /* Global font and background */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        font-weight: 700 !important;
    }
    /* Upload and button tweaks */
    .stButton>button {
        background: linear-gradient(90deg, #e30613, #b0000d);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-size: 16px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #b0000d, #7a0009);
        transform: scale(1.02);
    }
    /* Download buttons */
    .stDownloadButton>button {
        border-radius: 8px;
        border: 1px solid #ddd;
        background-color: white;
        color: #333;
        font-weight: 500;
        padding: 0.5em 1em;
    }
    .stDownloadButton>button:hover {
        background-color: #f8f9fa;
        border-color: #e30613;
        color: #e30613;
    }
    /* Card style for summary */
    .summary-card {
        padding: 20px;
        border-radius: 15px;
        background: #ffffff;
        border: 1px solid #eee;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        max-width: 650px;
        margin: 20px auto;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Header with Logo
# ------------------------
LOGO_PATH = "revolt_logo.png"  # Place logo file in repo

logo_html = ""
if os.path.exists(LOGO_PATH):
    logo_html = f'<img src="{LOGO_PATH}" width="120" style="margin-right:15px;">'

st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:center; margin-bottom:10px;">
        {logo_html}
        <h1 style="color:#222; margin:0;">Revolt Motors Data Cleaner</h1>
    </div>
    <p style="text-align:center; color:#666; font-size:16px;">
        Upload raw Excel/CSV → get a <b>cleaned dataset</b>, <b>flagged log</b>, and an <b>updated blocklist</b>.
    </p>
    <hr style="margin:20px 0;">
    """,
    unsafe_allow_html=True
)

# ------------------------
# File Upload
# ------------------------
uploaded_file = st.file_uploader("📂 Upload your Excel/CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    cleaned_output = "cleaned_output.xlsx"
    flagged_log = "flagged_log.txt"

    if st.button("🚀 Run Cleaning", use_container_width=True):
        # Run backend cleaning
        new_count = process_file(input_path, cleaned_output, flagged_log)

        # Compute stats
        cleaned_df = pd.ExcelFile(cleaned_output)
        total_rows = sum(len(cleaned_df.parse(sheet)) for sheet in cleaned_df.sheet_names)
        original_file = pd.ExcelFile(input_path)
        orig_rows = sum(len(original_file.parse(sheet)) for sheet in original_file.sheet_names)
        removed_rows = orig_rows - total_rows
        flagged_rows = sum(1 for _ in open(flagged_log, encoding="utf-8")) - 1
        blocklist_size = sum(1 for _ in open("seen_feedback_mobiles.csv", encoding="utf-8")) - 1

        # ------------------------
