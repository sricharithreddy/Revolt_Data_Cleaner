import streamlit as st
import pandas as pd
import os
from datetime import datetime
from Revoltv11 import process_file, load_blocklist
import subprocess
import glob
import base64

# ====================================================
# Helper: Load logo as Base64
# ====================================================
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

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
# Streamlit Page Config
# ====================================================
st.set_page_config(page_title="Revolt Dashboard", layout="wide")

# ====================================================
# CSS Styling (Minimal & Professional)
# ====================================================
st.markdown(
    """
    <style>
        /* Background */
        .main {
            background-color: #f5f6f8;
        }
        /* Center content */
        .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 30px;
            max-width: 900px;
        }
        /* Upload container */
        .box {
            background: #ffffff;
            padding: 25px 35px;
            border-radius: 12px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            max-width: 480px;
            width: 100%;
            text-align: center;
            margin-top: 20px;
        }
        /* File uploader center alignment */
        div[data-testid="stFileUploader"] {
            display: flex;
            justify-content: center;
        }
        /* Run Button */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6em 1.2em;
            font-size: 15px;
            font-weight: 600;
            transition: 0.3s;
            margin-top: 20px;
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
            transform: scale(1.02);
        }
        /* Download buttons row */
        .downloads {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .downloads div.stDownloadButton button {
            border-radius: 8px;
            padding: 0.5em 1em;
            font-size: 14px;
        }
        /* Alerts formatting */
        .stAlert {
            text-align: left;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Logo (smaller size to fit fully)
# ====================================================
if os.path.exists("revolt_logo.png"):
    logo_base64 = get_base64_image("revolt_logo.png")
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin-bottom:5px;">
            <img src="data:image/png;base64,{logo_base64}" width="160">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning("⚠️ Revolt logo not found in repo. Please add revolt_logo.png")

# ====================================================
# Upload + Process Section (Compact Box)
# ====================================================
st.markdown('<div class="box">', unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"
    cleaned_output = f"cleaned_{timestamp}.xlsx"
    flagged_log = f"flagged_{timestamp}.txt"
    blocklist_file = "seen_feedback_mobiles.csv"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🚀 Run Cleaning"):
        st.info("⚡ Running cleaner, please wait...")
        result = process_file(input_path, cleaned_output, flagged_log)

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

        # Download buttons inline
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

st.markdown('</div>', unsafe_allow_html=True)  # close box
