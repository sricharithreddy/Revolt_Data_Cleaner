# streamlit_app.py
import streamlit as st
import pandas as pd
import io
import tempfile
import os
from typing import List, Dict

# Import process_file from your script (ensure file is in same repo)
# In your uploaded file it's called Revoltv11.py with process_file defined
from Revoltv11 import process_file  # make sure function name matches

st.set_page_config(page_title="Revolt Cleaner", layout="wide")

st.title("Revolt — Customer Data Cleaner (Streamlit)")

st.markdown("""
Upload an Excel (.xlsx/.xls) or CSV; the app will clean customer names, mobile numbers,
format `trcompleteddate` and `trscheduleactual`, and provide a cleaned Excel and flagged log.
""")

uploaded = st.file_uploader("Choose file", type=["xlsx", "xls", "csv"])
out_name = st.text_input("Output file prefix", value="Revolt_Cleaned")
run = st.button("Clean file")

if uploaded:
    st.write(f"Uploaded: {uploaded.name} — size: {uploaded.size} bytes")
    if run:
        with st.spinner("Cleaning..."):
            # Save uploaded file to a temporary file to let existing process_file use a path
            tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1])
            tmp_in.write(uploaded.getbuffer())
            tmp_in.flush()
            tmp_in.close()

            tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp_out.close()

            # Flagged log temp path
            tmp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
            tmp_log.close()

            try:
                # Call your existing function
                process_file(tmp_in.name, tmp_out.name, tmp_log.name)

                # Read out cleaned excel to bytes for download
                with open(tmp_out.name, "rb") as f:
                    cleaned_bytes = f.read()

                with open(tmp_log.name, "rb") as f:
                    log_bytes = f.read()

                st.success("Cleaning finished — download files below.")
                st.download_button("Download cleaned Excel",
                                   data=cleaned_bytes,
                                   file_name=f"{out_name}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                st.download_button("Download flagged log",
                                   data=log_bytes,
                                   file_name=f"{out_name}_flagged.csv",
                                   mime="text/csv")

                # Optionally show preview of first sheet
                try:
                    df_preview = pd.read_excel(tmp_out.name, sheet_name=0)
                    st.subheader("Preview (first sheet)")
                    st.dataframe(df_preview.head(10))
                except Exception:
                    st.info("Preview not available for this file format.")
            finally:
                # cleanup temps
                try:
                    os.unlink(tmp_in.name)
                    os.unlink(tmp_out.name)
                    os.unlink(tmp_log.name)
                except Exception:
                    pass
else:
    st.info("Upload a file to enable cleaning.")
