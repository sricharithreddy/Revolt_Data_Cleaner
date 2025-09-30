import streamlit as st
import pandas as pd
import os, glob, subprocess
from datetime import datetime
from Revoltv11 import process_file, load_blocklist

# ====================================================
# GitHub Auto-Commit for Blocklist (Remains the same)
# ====================================================
def commit_blocklist_to_github():
    try:
        # Use st.secrets for a production app, mock for local testing if needed
        token = st.secrets["GITHUB_TOKEN"]
        user = st.secrets["GITHUB_USER"]
        repo = st.secrets["GITHUB_REPO"]
        remote_url = f"https://{user}:{token}@github.com/{user}/{repo}.git"

        # Git configuration and setup
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
        st.warning(f"⚠️ Could not commit blocklist. Check git setup and GITHUB_TOKEN in secrets: {e}")

# ====================================================
# Auto-cleanup old files (Remains the same)
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
# Switched to 'wide' layout to give more space for left alignment to look good
st.set_page_config(page_title="Revolt Data Processor", page_icon="⚡", layout="wide")

# ====================================================
# CSS Styling - MODIFIED FOR LEFT ALIGNMENT
# ====================================================
st.markdown(
    """
    <style>
        /* General Layout & Background */
        .main { background-color: #ffffff; }

        /* Block Container: Content is now left-aligned */
        .block-container {
            padding-top: 30px;
            padding-bottom: 20px;
            text-align: left; /* Essential change */
        }
        
        /* Remove previous centering attempts on the image/logo */
        div.stImage > img {
            margin-left: 0 !important;
            margin-right: auto;
            display: block;
        }

        /* File Uploader: Align to the left of its container */
        div[data-testid="stFileUploader"] { 
            margin: 20px 0; /* Left align */
            max-width: 500px; 
        }

        /* Custom Button Style (Primary Action): Now left-aligned */
        div.stButton {
            text-align: left;
        }
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white; border: none; border-radius: 12px;
            padding: 0.8em 1.5em; font-size: 17px; font-weight: 700;
            margin-top: 25px; min-width: 250px;
            box-shadow: 0 4px 10px rgba(227, 6, 19, 0.4);
            transition: all 0.2s ease;
            width: auto; /* Allow button to shrink */
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
            box-shadow: 0 6px 15px rgba(227, 6, 19, 0.6);
            transform: translateY(-2px);
        }

        /* Result Box - Now left-aligned */
        .result-box {
            background: #fcfcfc;
            padding: 30px;
            border-radius: 15px;
            border-left: 5px solid #e30613;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            margin-top: 35px;
            text-align: left;
            max-width: 650px;
            margin-left: 0; /* Align left */
            margin-right: auto;
        }
        .result-box h4 {
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
            font-weight: 700;
        }
        
        /* Download Buttons Styling - Now left-aligned */
        .download-column-header {
            text-align: left; 
            font-weight: bold; 
            margin-bottom: 10px;
        }

    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Header (Logo + Title) - ALIGNED LEFT
# ====================================================

# This column structure ensures the header content lives neatly on the left
st.columns([1])[0].markdown('<div style="text-align: left;">', unsafe_allow_html=True)

if os.path.exists("revolt_logo.png"):
    st.image("revolt_logo.png", width=100) # Slightly smaller for left alignment
else:
    st.write("⚠️ Add revolt_logo.png to repo root")

st.markdown(
    """
    <h1 style="text-align: left; margin-top: 5px; font-weight: 700; color: #333; font-size: 32px;">
        Data Processor for AI
    </h1>
    <p style="text-align: left; color: #666; margin-bottom: 30px;">
        Clean, filter, and prepare your data for machine learning models.
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ====================================================
# Upload + Processing
# ====================================================
uploaded_file = st.file_uploader(
    "Upload Excel/CSV", 
    type=["xlsx", "xls", "csv"], 
    help="Limit 300MB per file: XLSX, XLS, CSV"
)

if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"
    cleaned_output = f"cleaned_{timestamp}.xlsx"
    flagged_log = f"flagged_{timestamp}.txt"
    blocklist_file = "seen_feedback_mobiles.csv"

    # Save the file
    try:
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())
    except Exception as e:
        st.error(f"Failed to save uploaded file: {e}")
        st.stop()
        
    # Button is no longer centered, it's just placed after the uploader
    if st.button("🚀 Run Processing"):
        with st.spinner("⚡ Processing in progress..."):
            try:
                result = process_file(input_path, cleaned_output, flagged_log)
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
                result = None

        if result:
            # ================================
            # Summary Card Calculation
            # ================================
            # (Calculation logic remains the same)
            try:
                cleaned_df = pd.ExcelFile(cleaned_output)
                total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
            except:
                total_rows = 0
            
            try:
                orig_df = pd.ExcelFile(input_path)
                orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
            except:
                orig_rows = 0
                
            removed_rows = orig_rows - total_rows
            total_blocklist = len(load_blocklist())

            # ================================
            # Summary Card (Aligned Left)
            # ================================
            st.markdown(
                f"""
                <div class="result-box">
                <h4>✅ Processing Complete</h4>
                
                <div style="display: flex; justify-content: space-between; gap: 20px; padding-bottom: 10px;">
                    <div style="flex: 1; border-right: 1px solid #eee;">
                        <p style="font-size: 16px; margin-bottom: 5px; color: #555;"><b>Processed Rows</b></p>
                        <h2 style="color: #333; margin-top: 0; font-size: 28px;">{orig_rows}</h2>
                    </div>
                    <div style="flex: 1; border-right: 1px solid #eee;">
                        <p style="font-size: 16px; margin-bottom: 5px; color: #555;"><b>Cleaned Rows</b></p>
                        <h2 style="color: #008000; margin-top: 0; font-size: 28px;">{total_rows}</h2>
                    </div>
                    <div style="flex: 1;">
                        <p style="font-size: 16px; margin-bottom: 5px; color: #555;"><b>New Blocklisted</b></p>
                        <h2 style="color: #e30613; margin-top: 0; font-size: 28px;">+{result['new_numbers']}</h2>
                    </div>
                </div>
                
                <hr style="margin-top: 10px; margin-bottom: 15px; border-color: #eee;">
                
                <p style="text-align: left; font-size: 14px; color: #555;">
                    * <b>Removed Rows:</b> {removed_rows} (due to blocklist filtering)
                    <br>
                    * <b>Total Blocklist Size:</b> {total_blocklist} entries.
                </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ================================
            # Downloads Section (Aligned Left)
            # ================================
            st.markdown("---")
            st.markdown('<h4>Download Results</h4>', unsafe_allow_html=True)
            
            # Create a 3-column layout for the downloads
            col1, col2, col3, col_pad = st.columns([1, 1, 1, 2]) # Added padding column for wide layout
            
            # Cleaned file
            with col1:
                st.markdown('<div class="download-column-header">Cleaned Data</div>', unsafe_allow_html=True)
                if os.path.exists("cleaned_logo.png"):
                    st.image("cleaned_logo.png", width=50)
                with open(cleaned_output, "rb") as f:
                    st.download_button("⬇️ Download Cleaned", f, file_name=f"cleaned_{timestamp}.xlsx")

            # Flagged log
            with col2:
                st.markdown('<div class="download-column-header">Flagged Log</div>', unsafe_allow_html=True)
                if os.path.exists("flagged_logo.png"):
                    st.image("flagged_logo.png", width=50)
                with open(flagged_log, "rb") as f:
                    st.download_button("⬇️ Download Flagged", f, file_name=f"flagged_{timestamp}.txt")

            # Blocklist
            with col3:
                st.markdown('<div class="download-column-header">Updated Blocklist</div>', unsafe_allow_html=True)
                if os.path.exists("blocklist_logo.png"):
                    st.image("blocklist_logo.png", width=50)
                with open(blocklist_file, "rb") as f:
                    st.download_button("⬇️ Download Blocklist", f, file_name=f"blocklist_{timestamp}.csv")
            
            st.markdown("---")
            
            # GitHub Commit + Cleanup
            commit_blocklist_to_github()
            cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])
```
