import streamlit as st
import pandas as pd
import tempfile, os, io
import json
from Revoltv11 import process_file  # your existing cleaning logic

st.set_page_config(page_title="Revolt Cleaner", layout="wide")

st.title("Revolt — Customer Data Cleaner")
st.write("Upload Excel/CSV and get cleaned workbook + flagged log.")

# Upload
uploaded = st.file_uploader("Upload Excel/CSV", type=["xlsx", "xls", "csv"])
out_name = st.text_input("Output file prefix", value="Revolt_Cleaned")

# Column rename editor
st.subheader("Optional: Column Name Changes")
st.markdown(
    """
Default conditions applied:
- `mobilenumber` → `Mobile Number`  
- `buyername` → `Customer Name`  
- `testridedateandtimeactual` → `trscheduleactual`

You can add more rules here, one per line, in the format:
```
old_column -> New Column
```
"""
)
rename_rules_text = st.text_area(
    "Column rename rules", 
    value="mobilenumber -> Mobile Number\nbuyername -> Customer Name\ntestridedateandtimeactual -> trscheduleactual",
    height=120
)

# Parse rules into dict
def parse_rules(text: str):
    mapping = {}
    for line in text.splitlines():
        if "->" in line:
            old, new = line.split("->", 1)
            old, new = old.strip(), new.strip()
            if old and new:
                mapping[old.lower()] = new
    return mapping

rename_rules = parse_rules(rename_rules_text)
os.environ["REVOLT_RENAMES"] = json.dumps(rename_rules)

# Run cleaner
if uploaded and st.button("Run Cleaner"):
    with st.spinner("Cleaning in progress..."):
        suffix = os.path.splitext(uploaded.name)[1]
        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_in.write(uploaded.getbuffer())
        tmp_in.flush()
        tmp_in.close()

        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp_out.close()
        tmp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp_log.close()

        try:
            process_file(tmp_in.name, tmp_out.name, tmp_log.name)

            with open(tmp_out.name, "rb") as f:
                cleaned_bytes = f.read()
            with open(tmp_log.name, "rb") as f:
                log_bytes = f.read()

            st.success("Cleaning completed. Download results below:")
            st.download_button("📥 Download cleaned Excel", cleaned_bytes, f"{out_name}.xlsx")
            st.download_button("📥 Download flagged log", log_bytes, f"{out_name}_flagged.csv")
        finally:
            for fn in (tmp_in.name, tmp_out.name, tmp_log.name):
                try:
                    os.unlink(fn)
                except:
                    pass
