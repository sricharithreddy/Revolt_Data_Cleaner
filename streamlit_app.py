import streamlit as st
import os
import tempfile
import pandas as pd
from Revoltv11 import process_file

st.set_page_config(page_title="Revolt Data Cleaner", layout="centered")
st.title("⚡ Revolt Motors Data Cleaner")

st.markdown(
    "<p style='color:gray'>Upload raw Excel/CSV data → get cleaned file, flagged log, and updated blocklist.</p>",
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("📂 Upload your Excel/CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    cleaned_output = "cleaned_output.xlsx"
    flagged_log = "flagged_log.txt"

    if st.button("🚀 Run Cleaning", use_container_width=True):
        # Run cleaning and capture blocklist updates
        new_count = process_file(input_path, cleaned_output, flagged_log)

        # Count stats
        cleaned_df = pd.ExcelFile(cleaned_output)
        total_rows = sum(len(cleaned_df.parse(sheet)) for sheet in cleaned_df.sheet_names)
        flagged_rows = sum(1 for _ in open(flagged_log, encoding="utf-8")) - 1  # minus header
        blocklist_size = sum(1 for _ in open("seen_feedback_mobiles.csv", encoding="utf-8")) - 1

        # Calculate removed rows
        original_file = pd.ExcelFile(input_path)
        orig_rows = sum(len(original_file.parse(sheet)) for sheet in original_file.sheet_names)
        removed_rows = orig_rows - total_rows

        # --- Process Summary Panel ---
        with st.container():
            st.markdown(
                """
                <div style="padding:15px; border-radius:12px; background-color:#f8f9fa; border:1px solid #ddd;">
                <h4 style="margin-top:0;">📊 Process Summary</h4>
                <p>✅ Processed: <b>{orig}</b> rows</p>
                <p>📤 Cleaned File: <b>{cleaned}</b> rows</p>
                <p>🚫 Removed (blocklisted): <b>{removed}</b> rows</p>
                <p>📋 Blocklist: +<b>{new}</b> new (now total <b>{total}</b>)</p>
                </div>
                """.format(
                    orig=orig_rows,
                    cleaned=total_rows,
                    removed=removed_rows,
                    new=new_count,
                    total=blocklist_size
                ),
                unsafe_allow_html=True
            )

        # --- Downloads Section ---
        st.subheader("📥 Downloads")

        if os.path.exists(cleaned_output):
            with open(cleaned_output, "rb") as f:
                st.download_button(
                    "⬇️ Download Cleaned File",
                    f,
                    file_name="cleaned_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        if os.path.exists(flagged_log):
            with open(flagged_log, "rb") as f:
                st.download_button(
                    "⬇️ Download Flagged Log",
                    f,
                    file_name="flag_
