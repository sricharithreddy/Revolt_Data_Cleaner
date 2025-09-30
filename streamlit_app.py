import streamlit as st
import os
import tempfile
import pandas as pd
from datetime import datetime
from Revoltv11 import process_file

# Path or URL to logo (if you host it or embed in repo)
LOGO_PATH = "revolt_logo.png"  # place logo file in your repo directory

st.set_page_config(page_title="Revolt Data Cleaner", layout="centered")

# Header with logo + title
logo_html = ""
if os.path.exists(LOGO_PATH):
    logo_html = f'<img src="{LOGO_PATH}" width="120" style="margin-right:10px; vertical-align:middle;">'
st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:center;">
        {logo_html}
        <h1 style="color:#333; margin:0;">Revolt Motors Data Cleaner</h1>
    </div>
    <p style="text-align:center; color:gray; font-size:16px;">
        Upload raw Excel/CSV → get cleaned dataset, flagged log & updated blocklist
    </p>
    <hr style="margin:20px 0;">
    """,
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("📂 Upload your Excel / CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    cleaned_output = "cleaned_output.xlsx"
    flagged_log = "flagged_log.txt"

    if st.button("🚀 Run Cleaning", use_container_width=True):
        new_count = process_file(input_path, cleaned_output, flagged_log)

        # compute stats
        cleaned_excel = pd.ExcelFile(cleaned_output)
        total_rows = sum(len(cleaned_excel.parse(s)) for s in cleaned_excel.sheet_names)
        original_excel = pd.ExcelFile(input_path)
        orig_rows = sum(len(original_excel.parse(s)) for s in original_excel.sheet_names)
        removed_rows = orig_rows - total_rows

        flagged_count = 0
        if os.path.exists(flagged_log):
            with open(flagged_log, encoding="utf-8") as f:
                flagged_count = sum(1 for _ in f) - 1  # minus header

        blocklist_size = 0
        if os.path.exists("seen_feedback_mobiles.csv"):
            with open("seen_feedback_mobiles.csv", encoding="utf-8") as f:
                blocklist_size = sum(1 for _ in f) - 1

        # Summary card
        st.markdown(
            f"""
            <div style="
                padding:20px;
                border-radius:12px;
                background-color:#f8f9fa;
                border:1px solid #ddd;
                box-shadow:0 2px 8px rgba(0,0,0,0.05);
                margin-top:20px;
                max-width:600px;
                margin-left:auto;
                margin-right:auto;
            ">
                <h3 style="margin-top:0; color:#444;">📊 Process Summary</h3>
                <p>✅ Processed: <b>{orig_rows:,}</b> rows</p>
                <p>📤 Cleaned File: <b>{total_rows:,}</b> rows</p>
                <p>🚫 Removed (blocklisted): <b>{removed_rows:,}</b> rows</p>
                <p>📋 Blocklist: +<b>{new_count:,}</b> new (now total <b>{blocklist_size:,}</b>)</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<h3 style='margin-top:30px;'>📥 Downloads</h3>", unsafe_allow_html=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if os.path.exists(cleaned_output):
            with open(cleaned_output, "rb") as f:
                st.download_button(
                    "⬇️ Download Cleaned File",
                    f,
                    file_name=f"cleaned_output_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        if os.path.exists(flagged_log):
            with open(flagged_log, "rb") as f:
                st.download_button(
                    "⬇️ Download Flagged Log",
                    f,
                    file_name=f"flagged_log_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        if os.path.exists("seen_feedback_mobiles.csv"):
            with open("seen_feedback_mobiles.csv", "rb") as f:
                st.download_button(
                    "⬇️ Download Blocklist",
                    f,
                    file_name=f"seen_feedback_mobiles_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
