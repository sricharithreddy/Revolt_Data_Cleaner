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
st.set_page_config(page_title="Revolt Data Processor", page_icon="⚡", layout="centered")

# ====================================================
# CSS Styling
# ====================================================
st.markdown(
    """
    <style>
        .main { background-color: #f5f6f8; }

        .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 25px;
            text-align: center;
        }

        div[data-testid="stFileUploader"] { margin: 0 auto; }

        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white; border: none; border-radius: 8px;
            padding: 0.7em 1.2em; font-size: 16px; font-weight: 600;
            margin-top: 15px; width: 100%;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
        }

        .result-box {
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-top: 20px;
            text-align: left;
        }

        .download-grid {
            display: flex; justify-content: center; gap: 20px; margin-top: 20px; flex-wrap: wrap;
        }
        .download-card {
            background: #fff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            width: 180px; text-align: center;
        }
        .download-card img {
            height: 40px; margin-bottom: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Logo + Subtitle (stacked, centered)
# ====================================================
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 25px;">
        <img src="revolt_logo.png" alt="Revolt Logo" style="height: 70px; margin-bottom: 10px;">
        <h3 style="margin: 0; font-weight: 600; color: #333;">Data Processor for AI</h3>
    </div>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Upload + Processing
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

    if st.button("🚀 Run Processing"):
        with st.spinner("⚡ Processing in progress..."):
            result = process_file(input_path, cleaned_output, flagged_log)

            # ================================
            # Summary Card
            # ================================
            cleaned_df = pd.ExcelFile(cleaned_output)
            total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
            orig_df = pd.ExcelFile(input_path)
            orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
            removed_rows = orig_rows - total_rows

            st.markdown(
                f"""
                <div class="result-box">
                <h4>✅ Processing Complete</h4>
                <ul>
                    <li><b>Processed:</b> {orig_rows} rows</li>
                    <li><b>Cleaned File:</b> {total_rows} rows</li>
                    <li><b>Removed (blocklisted):</b> {removed_rows} rows</li>
                    <li><b>Blocklist Update:</b> +{result['new_numbers']} new  
                        (Now total: {len(load_blocklist())})</li>
                </ul>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ================================
            # Downloads Section
            # ================================
            st.markdown('<div class="download-grid">', unsafe_allow_html=True)

            # Cleaned file
            with open(cleaned_output, "rb") as f:
                st.markdown('<div class="download-card">', unsafe_allow_html=True)
                if os.path.exists("cleaned_logo.png"):
                    st.image("cleaned_logo.png")
                st.download_button("⬇️ Cleaned", f, file_name=f"cleaned_{timestamp}.xlsx")
                st.markdown('</div>', unsafe_allow_html=True)

            # Flagged log
            with open(flagged_log, "rb") as f:
                st.markdown('<div class="download-card">', unsafe_allow_html=True)
                if os.path.exists("flagged_logo.png"):
                    st.image("flagged_logo.png")
                st.download_button("⬇️ Flagged", f, file_name=f"flagged_{timestamp}.txt")
                st.markdown('</div>', unsafe_allow_html=True)

            # Blocklist
            with open(blocklist_file, "rb") as f:
                st.markdown('<div class="download-card">', unsafe_allow_html=True)
                if os.path.exists("blocklist_logo.png"):
                    st.image("blocklist_logo.png")
                st.download_button("⬇️ Blocklist", f, file_name=f"blocklist_{timestamp}.csv")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # GitHub Commit + Cleanup
            commit_blocklist_to_github()
            cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])
