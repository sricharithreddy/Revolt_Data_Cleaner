import streamlit as st
import os
import tempfile
from Revoltv11 import process_file

st.set_page_config(page_title="Revolt Data Cleaner", layout="centered")
st.title("⚡ Revolt Motors Data Cleaner")

uploaded_file = st.file_uploader("Upload your Excel/CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    cleaned_output = "cleaned_output.xlsx"
    flagged_log = "flagged_log.txt"

    if st.button("🚀 Run Cleaning"):
        new_count = process_file(input_path, cleaned_output, flagged_log)

        # Show info about blocklist update
        if new_count > 0:
            st.info(f"✅ Blocklist updated with {new_count} new numbers.")
        else:
            st.info("ℹ️ No new numbers were added to the blocklist this run.")

        # Download cleaned file
        if os.path.exists(cleaned_output):
            with open(cleaned_output, "rb") as f:
                st.download_button(
                    "⬇️ Download Cleaned File",
                    f,
                    file_name="cleaned_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # Download flagged log
        if os.path.exists(flagged_log):
            with open(flagged_log, "rb") as f:
                st.download_button(
                    "⬇️ Download Flagged Log",
                    f,
                    file_name="flagged_log.txt",
                    mime="text/plain"
                )

        # Download blocklist
        if os.path.exists("seen_feedback_mobiles.csv"):
            with open("seen_feedback_mobiles.csv", "rb") as f:
                st.download_button(
                    "⬇️ Download Blocklist",
                    f,
                    file_name="seen_feedback_mobiles.csv",
                    mime="text/csv"
                )
