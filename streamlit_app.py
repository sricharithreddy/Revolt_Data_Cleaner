import streamlit as st
import pandas as pd
import os
from datetime import datetime
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

        # Configure git
        subprocess.run(["git", "config", "--global", "user.email", f"{user}@users.noreply.github.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", user], check=True)

        # Stage the file
        subprocess.run(["git", "add", "seen_feedback_mobiles.csv"], check=True)

        # Check if changes exist
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if "seen_feedback_mobiles.csv" not in status.stdout:
            st.info("ℹ️ No changes in blocklist, skipping commit.")
            return

        # Commit and push
        subprocess.run(["git", "commit", "-m", "Update blocklist [auto-commit]"], check=True)
        subprocess.run(["git", "push", remote_url, "main"], check=True)

        st.success("✅ Blocklist committed to GitHub successfully.")
    except Exception as e:
        st.warning(f"⚠️ Could not commit blocklist: {e}")

# ====================================================
# Auto-cleanup old files
# ====================================================
def cleanup_old_files(keep_files):
    """Delete all uploaded/cleaned/log files except current ones."""
    patterns = ["uploaded_*.xlsx", "cleaned_*.xlsx", "flagged_*.txt"]
    for pattern in patterns:
        for f in glob.glob(pattern):
            if f not in keep_files:
                try:
                    os.remove(f)
                except Exception:
                    pass

# ====================================================
# Streamlit Page Config
# ====================================================
st.set_page_config(page_title="Revolt Data Cleaner", layout="wide")

# Custom CSS (CTA button styling)
st.markdown(
    """
    <style>
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6em 1.2em;
            font-size: 16px;
            font-weight: 600;
            transition: 0.3s;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
            transform: scale(1.02);
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Properly Centered Logo
# ====================================================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("revolt_logo.png"):
        st.image("revolt_logo.png", width=180)
    else:
        st.warning("⚠️ Revolt logo not found in repo. Please add revolt_logo.png")

# ====================================================
# File Upload
# ====================================================
st.markdown("### 📂 Upload Excel File")
uploaded_file = st.file_uploader("Choose a file", type=["xlsx"])

if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"
    cleaned_output = f"cleaned_{timestamp}.xlsx"
    flagged_log = f"flagged_{timestamp}.txt"
    blocklist_file = "seen_feedback_mobiles.csv"  # master file

    # Save uploaded file locally
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    # CTA button
    if st.button("🚀 Run Cleaning", use_container_width=True):
        st.info("⚡ Running cleaner, please wait...")
        result = process_file(input_path, cleaned_output, flagged_log)

        # Load sizes
        cleaned_df = pd.ExcelFile(cleaned_output)
        total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
        orig_df = pd.ExcelFile(input_path)
        orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
        removed_rows = orig_rows - total_rows

        # Process summary
        st.markdown("### 📊 Process Summary")
        st.success(
            f"""
            ✅ Processed: {orig_rows} rows  
            📤 Cleaned File: {total_rows} rows  
            🚫 Removed (blocklisted): {removed_rows} rows  
            📋 Blocklist: +{result['new_numbers']} new (now total {len(load_blocklist())})
            """
        )

        # Download buttons with timestamped names
        with open(cleaned_output, "rb") as f:
            st.download_button("⬇️ Download Cleaned File", f, file_name=f"cleaned_{timestamp}.xlsx")

        with open(flagged_log, "rb") as f:
            st.download_button("⬇️ Download Flagged Log", f, file_name=f"flagged_{timestamp}.txt")

        with open(blocklist_file, "rb") as f:
            st.download_button("⬇️ Download Blocklist", f, file_name=f"blocklist_{timestamp}.csv")

        # Commit blocklist back to GitHub
        commit_blocklist_to_github()

        # Cleanup old temp files
        cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])
