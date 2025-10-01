import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from Revoltv11 import process_file, load_blocklist
import subprocess
import glob

# ====================================================
# GitHub Auto-Commit for Blocklist
# ====================================================
def commit_blocklist_to_github():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        user = st.secrets["GITHUB_USER"]
        repo = st.secrets["GITHUB_REPO"]

        remote_url = f"https://{user}:{token}@github.com/{user}/{repo}.git"

        subprocess.run(["git", "config", "--global", "user.email", f"{user}@users.noreply.github.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", user], check=True)

        subprocess.run(["git", "add", "seen_feedback_mobiles.csv"], check=True)

        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if "seen_feedback_mobiles.csv" not in status.stdout:
            st.info("ℹ️ No changes in blocklist, skipping commit.")
            return

        subprocess.run(["git", "commit", "-m", "Update blocklist [auto-commit]"], check=True)
        subprocess.run(["git", "push", remote_url, "main"], check=True)

        st.success("✅ Blocklist committed to GitHub successfully.")
    except Exception as e:
        st.warning(f"⚠️ Could not commit blocklist: {e}")

# ====================================================
# Auto-cleanup old files
# ====================================================
def cleanup_old_files(keep_files):
    patterns = ["uploaded_*.xlsx", "cleaned_*.xlsx", "flagged_*.txt"]
    for pattern in patterns:
        for f in glob.glob(pattern):
            if f not in keep_files:
                try:
                    os.remove(f)
                except Exception:
                    pass

# ====================================================
# Page Config
# ====================================================
st.set_page_config(page_title="Revolt Data Processor", layout="wide")

# ====================================================
# Revolt Branding (Logo + Title)
# ====================================================
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if os.path.exists("revolt_logo.png"):
        st.image("revolt_logo.png", width=180)
    st.markdown("<h3 style='text-align: center; color: #e30613;'>Data Processor for AI</h3>", unsafe_allow_html=True)

st.divider()

# ====================================================
# File Upload + Blocklist Options
# ====================================================
with st.container(border=True):
    st.markdown("### 📂 Upload Excel File")

    uploaded_file = st.file_uploader("Choose a file", type=["xlsx","xls","csv"], label_visibility="collapsed")

    st.markdown("### ⚙️ Blocklist Options")
    use_blocklist = st.checkbox("Apply Blocklist Filtering", value=True)
    cutoff_date = None
    if use_blocklist:
        cutoff_date = st.date_input("Blocklist Cutoff Date", value=datetime.today() - timedelta(days=1))

# ====================================================
# Run Processing
# ====================================================
if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"
    cleaned_output = f"cleaned_{timestamp}.xlsx"
    flagged_log = f"flagged_{timestamp}.txt"
    blocklist_file = "seen_feedback_mobiles.csv"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🚀 Run Cleaning", use_container_width=True, type="primary"):
        st.info("⚡ Running cleaner, please wait...")

        # Run backend
        result = process_file(
            input_path,
            cleaned_output,
            flagged_log,
            apply_blocklist=use_blocklist,
            cutoff_date=cutoff_date
        )

        # ====================================================
        # Process Summary
        # ====================================================
        with st.container(border=True):
            st.subheader("📊 Process Summary")

            cleaned_df = pd.ExcelFile(cleaned_output)
            total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
            orig_df = pd.ExcelFile(input_path)
            orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
            removed_rows = orig_rows - total_rows if use_blocklist else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("✅ Processed", orig_rows)
            m2.metric("🧹 Cleaned", total_rows)
            m3.metric("⛔ Removed (Blocklist)", removed_rows if use_blocklist else "N/A")
            m4.metric("📋 New Blocklist", result["new_numbers"] if use_blocklist else "N/A")

            c1, c2, c3 = st.columns(3)
            c1.metric("✏️ Names Fixed", result["name_fixes"])
            c2.metric("📱 Mobiles Fixed", result["mobile_fixes"])
            c3.metric("⚠️ Invalid Cases", result["invalid_cases"])

        # ====================================================
        # Downloads
        # ====================================================
        with st.container(border=True):
            st.subheader("⬇️ Downloads")
            d1, d2, d3 = st.columns(3)

            with d1:
                with open(cleaned_output, "rb") as f:
                    st.download_button("✅ Cleaned File", f, file_name=f"cleaned_{timestamp}.xlsx", use_container_width=True)

            with d2:
                with open(flagged_log, "rb") as f:
                    st.download_button("⚠️ Flagged Log", f, file_name=f"flagged_{timestamp}.txt", use_container_width=True)

            with d3:
                with open(blocklist_file, "rb") as f:
                    st.download_button("⛔ Blocklist", f, file_name=f"blocklist_{timestamp}.csv", use_container_width=True)

        # ====================================================
        # Commit blocklist back to GitHub
        # ====================================================
        if use_blocklist:
            commit_blocklist_to_github()

        # ====================================================
        # Cleanup temp files
        # ====================================================
        cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])
