import streamlit as st
import pandas as pd
import os
from datetime import datetime
from Revoltv11 import process_file, load_blocklist
import subprocess

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
# Streamlit Page Config
# ====================================================
st.set_page_config(page_title="Revolt Data Cleaner", layout="wide")

# Header with logo
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: center; padding: 10px 0;">
        <img src="https://raw.githubusercontent.com/streamlit/brand/main/logos/mark/streamlit-mark-primary.png" 
             alt="Revolt Logo" style="height:80px; margin-right: 15px;">
        <h1 style="color:#e30613; margin:0;">Revolt Motors Data Cleaner</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

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

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    st.info("⚡ Running cleaner, please wait...")
    result = process_file(input_path, cleaned_output, flagged_log)

    # Load sizes
    cleaned_df = pd.ExcelFile(cleaned_output)
    total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
    orig_df = pd.ExcelFile(input_path)
    orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
    removed_rows = orig_rows - total_rows

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

    with open("seen_feedback_mobiles.csv", "rb") as f:
        st.download_button("⬇️ Download Blocklist", f, file_name=f"blocklist_{timestamp}.csv")

    commit_blocklist_to_github()
