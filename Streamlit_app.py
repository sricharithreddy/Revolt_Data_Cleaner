import streamlit as st
import pandas as pd
import io, tempfile, os, json
from typing import List, Dict, Optional
from Revoltv11 import process_file  # your cleaning logic; ensure it reads env vars for settings if needed

# Page config
st.set_page_config(page_title="Revolt Cleaner", layout="wide", initial_sidebar_state="collapsed")

# Small CSS to make UI look professional and clean
st.markdown(
    """
    <style>
    .stApp { background: #f7fafc; color: #0f172a; }
    .header { padding: 18px 24px; border-radius: 10px; background: linear-gradient(90deg,#0ea5a4 0%, #06b6d4 100%); color: white; }
    .card { background: white; padding: 18px; border-radius: 10px; box-shadow: 0 4px 18px rgba(12,24,40,0.06); }
    .muted { color: #64748b; }
    .small { font-size: 0.9rem; color: #475569; }
    .input-label { font-weight:600; color:#0f172a; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="header"><h2 style="margin:0">Revolt — Customer Data Cleaner</h2><div class="muted">Clean lead data quickly & safely</div></div>', unsafe_allow_html=True)
st.markdown("<br/>", unsafe_allow_html=True)

# Layout: two columns (main and side actions)
main_col, side_col = st.columns([3,1])

with main_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Upload & Clean")
    st.write("Upload an Excel (.xlsx/.xls) or CSV file. The cleaner will process all sheets and return a cleaned workbook and a flagged log.")
    uploaded = st.file_uploader("Choose file", type=["xlsx","xls","csv"], accept_multiple_files=False)
    out_prefix = st.text_input("Output filename prefix", value="Revolt_Cleaned", max_chars=60)
    # Hyphen behavior option (small toggle)
    hyphen_choice = st.radio("Hyphen handling", options=["Remove hyphens (Mary-Anne -> MaryAnne)", "Convert hyphens to space (Mary-Anne -> Mary Anne)"], index=0, horizontal=True)
    date_choice = st.selectbox("Date output", ["Day + Month (21st September)", "Full long date (21st September 2025)"])
    st.markdown("<hr/>", unsafe_allow_html=True)
    # Blacklist editor
    st.markdown("**Blacklist (comma separated)** — names to flag/ignore, whole-word matches. Example: lead, test, hotel")
    blacklist_input = st.text_area("Blacklist", value="lead, test, dummy, na, abc, hotel", height=80)
    st.markdown("<hr/>", unsafe_allow_html=True)
    # Column renaming editor (optional)
    st.markdown("**Optional column renames** — one per line, format `current_name -> New Name` (case-insensitive, ignores spaces/underscores).")
    st.markdown("<div class='small muted'>Example: mobilenumber -> Mobile Number</div>", unsafe_allow_html=True)
    renames_input = st.text_area("Column renames", value="mobilenumber -> Mobile Number\nbuyername -> Customer Name\ntestridedateandtimeactual -> trscheduleactual", height=120)
    st.markdown("<hr/>", unsafe_allow_html=True)
    run = st.button("Run cleaning", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with side_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Actions & Sample")
    st.markdown("Download a small sample file to test the cleaner.")
    if st.button("Download sample Excel"):
        sample = pd.DataFrame({
            "Customer Name": ["S U R A J", "Mary-Anne", "--Lead", "RAJPUT", "O'Connor"],
            "Mobile Number": ["+91-9876543210", "00919876543210", "12345", "91 98765 43210", "9876543210"],
            "trcompleteddate": ["2025-09-21 00:00:00", "2025-03-03 00:00:00", None, "2025-08-15 00:00:00", "2025-12-01 00:00:00"]
        })
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            sample.to_excel(writer, index=False, sheet_name="Sheet1")
        towrite.seek(0)
        st.download_button("Download sample", towrite.getvalue(), file_name="revolt_sample.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("### Help")
    st.markdown("Need changes? Add blacklist items or column rename rules above and re-run. Logs are available for download after each run.")
    st.markdown("</div>", unsafe_allow_html=True)

# Process renames input into JSON string env var
def parse_renames(text: str) -> Dict[str, str]:
    mapping = {}
    for line in text.splitlines():
        if "->" in line:
            left, right = line.split("->", 1)
            left = left.strip().lower().replace(" ", "").replace("_", "")
            right = right.strip()
            if left and right:
                mapping[left] = right
    return mapping

renames_map = parse_renames(renames_input)
# Set environment variables for the cleaning logic to read (if Revoltv11 supports env vars)
os.environ["REVOLT_HYPHEN_BEHAVIOR"] = "remove" if hyphen_choice.startswith("Remove") else "space"
os.environ["REVOLT_DATE_FORMAT"] = "day_month" if date_choice.startswith("Day") else "long"
os.environ["REVOLT_BLACKLIST"] = ",".join([t.strip().lower() for t in blacklist_input.split(",") if t.strip()])
os.environ["REVOLT_RENAMES"] = json.dumps(renames_map)

# Run processing when requested
if run:
    if not uploaded:
        st.warning("Please upload a file before running.")
    else:
        st.info("Running cleaner — this may take a few seconds depending on file size.")
        try:
            suffix = os.path.splitext(uploaded.name)[1]
            tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp_in.write(uploaded.getbuffer())
            tmp_in.flush()
            tmp_in.close()

            tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp_out.close()
            tmp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            tmp_log.close()

            # Call your cleaning function. It should read the environment variables for behavior.
            process_file(tmp_in.name, tmp_out.name, tmp_log.name)

            # Prepare downloads
            with open(tmp_out.name, "rb") as f:
                cleaned_bytes = f.read()
            with open(tmp_log.name, "rb") as f:
                log_bytes = f.read()

            st.success("Cleaning completed. Download files below.")
            st.download_button("Download cleaned Excel", data=cleaned_bytes,
                               file_name=f"{out_prefix}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            st.download_button("Download flagged log", data=log_bytes,
                               file_name=f"{out_prefix}_flagged.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Error during processing: {e}")
        finally:
            # cleanup temporary files
            try:
                os.unlink(tmp_in.name)
                os.unlink(tmp_out.name)
                os.unlink(tmp_log.name)
            except Exception:
                pass

st.markdown("<br/>", unsafe_allow_html=True)
st.markdown('<div class="small muted">Questions or customizations? Ask me to add persistent blacklist, theme tweaks, or admin features.</div>', unsafe_allow_html=True)
