import streamlit as st
import pandas as pd
import os
from datetime import datetime
from Revoltv11 import process_file

# ====================================================
# Page Setup
# ====================================================
st.set_page_config(page_title="Revolt TD Processor", layout="wide")

st.title("⚡ Revolt TD Data Processor")
st.markdown("Upload your TR Excel file below to generate TD Reminder and Feedback files in standard Calls format.")

# ====================================================
# File Upload
# ====================================================
uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx", "xls"], label_visibility="collapsed")

# ====================================================
# Run Processing
# ====================================================
if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🚀 Run Cleaning and Generate Files", use_container_width=True, type="primary"):
        st.info("⚡ Processing, please wait...")

        outputs = process_file(input_path)

        if not outputs:
            st.error("No valid sheets found in the uploaded file.")
        else:
            st.success("✅ Files generated successfully!")

            today = datetime.today().strftime("%d %b").lstrip("0")
            col1, col2 = st.columns(2)

            if "reminder" in outputs:
                with col1:
                    with open(outputs["reminder"], "rb") as f:
                        st.download_button(
                            "⬇️ Download TD Reminder File",
                            f,
                            file_name=f"Revolt TD Reminder {today}.xlsx",
                            use_container_width=True
                        )

            if "feedback" in outputs:
                with col2:
                    with open(outputs["feedback"], "rb") as f:
                        st.download_button(
                            "⬇️ Download TD Feedback File",
                            f,
                            file_name=f"Revolt TD Feedback {today}.xlsx",
                            use_container_width=True
                        )

        # Optional: Cleanup temp files
        try:
            os.remove(input_path)
        except Exception:
            pass
