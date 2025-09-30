import streamlit as st
import pandas as pd
import os, glob, subprocess
from datetime import datetime
from Revoltv11 import process_file, load_blocklist

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
                except:
                    pass

# ====================================================
# Page Setup
# ====================================================
st.set_page_config(page_title="Revolt Dashboard", page_icon="⚡", layout="centered")

# ====================================================
# CSS Styling (Minimal)
# ====================================================
st.markdown(
    """
    <style>
        .main { background-color: #f5f6f8; }
        .block-container { max-width: 600px; margin: auto; }

        /* Buttons */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white; border: none; border-radius: 8px;
            padding: 0.6em 1.2em; font-size: 15px; font-weight: 600;
            margin-top: 15px; width: 100%;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
        }

        /* Download buttons inline */
        .downloads { display: flex; justify-content: center; gap: 12px; margin-top: 15px; flex-wrap: wrap; }
    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Logo
# ====================================================
st.image("https://upload.wikimedia.org/wikipedia/commons/6/6e/Revolt_Motors_logo.png", width=130)

# ====================================================
# Upload + Process
# ====================================================
uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"
    cleaned_output = f"cleaned_{timestamp}.xlsx"
    flagged_log = f"flagged_{timestamp}.txt"
    blocklist_file = "seen_feedback_mobiles.csv"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🚀 Run Cleaning"):
        with st.spinner("⚡ Cleaning in progress..."):
            result = process_file(input_path, cleaned_output, flagged_log)

            # Summary
            cleaned_df = pd.ExcelFile(cleaned_output)
            total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
            orig_df = pd.ExcelFile(input_path)
            orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
            removed_rows = orig_rows - total_rows

            st.success(
                f"""
                ✅ **Processed:** {orig_rows} rows  
                📤 **Cleaned File:** {total_rows} rows  
                🚫 **Removed (blocklisted):** {removed_rows} rows  
                📋 **Blocklist Update:** +{result['new_numbers']} new  
                _(Now total: {len(load_blocklist())})_
                """
            )

            # Downloads
            st.markdown('<div class="downloads">', unsafe_allow_html=True)
            with open(cleaned_output, "rb") as f:
                st.download_button("⬇️ Cleaned", f, file_name=f"cleaned_{timestamp}.xlsx")
            with open(flagged_log, "rb") as f:
                st.download_button("⬇️ Flagged", f, file_name=f"flagged_{timestamp}.txt")
            with open(blocklist_file, "rb") as f:
                st.download_button("⬇️ Blocklist", f, file_name=f"blocklist_{timestamp}.csv")
            st.markdown('</div>', unsafe_allow_html=True)

            commit_blocklist_to_github()
            cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])
