import streamlit as st
import pandas as pd
import os, glob, subprocess
from datetime import datetime
from Revoltv11 import process_file, load_blocklist # Assuming this module is correct

# ====================================================
# GitHub Auto-Commit for Blocklist
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
        # Catch errors if running locally without secrets or git setup
        st.warning(f"⚠️ Could not commit blocklist. Check git setup and GITHUB_TOKEN in secrets: {e}")

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
# CSS Styling - IMPORVED FOR PROFESSIONALISM & CENTERING
# ====================================================
st.markdown(
    """
    <style>
        /* General Layout & Background */
        .main { background-color: #ffffff; } /* Pure white background for a clean look */

        /* Main Container for Centering */
        .block-container {
            padding-top: 30px;
            padding-bottom: 20px;
            /* Using centered layout, but ensure text is centered in the header */
            text-align: center;
        }

        /* Centering the File Uploader */
        div[data-testid="stFileUploader"] { margin: 20px auto; max-width: 500px; }

        /* Custom Button Style (Primary Action) */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white; border: none; border-radius: 12px;
            padding: 0.8em 1.5em; font-size: 17px; font-weight: 700;
            margin-top: 25px; min-width: 250px;
            box-shadow: 0 4px 10px rgba(227, 6, 19, 0.4);
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
            box-shadow: 0 6px 15px rgba(227, 6, 19, 0.6);
            transform: translateY(-2px);
        }

        /* Result Box - Modern, well-defined look */
        .result-box {
            background: #fcfcfc;
            padding: 30px;
            border-radius: 15px;
            border-left: 5px solid #e30613; /* Highlight color */
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            margin-top: 35px;
            text-align: left;
            max-width: 650px;
            margin-left: auto;
            margin-right: auto;
        }
        .result-box h4 {
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
            font-weight: 700;
        }
        .result-box ul {
            list-style-type: none;
            padding: 0;
            line-height: 1.8;
        }
        .result-box li {
            font-size: 16px;
            color: #555;
        }
        .result-box b {
            font-weight: 600;
            color: #222;
        }

        /* Download Buttons Styling */
        div.stDownloadButton > button {
            background-color: #007bff; /* Generic secondary action color, or a lighter red */
            color: white; border: none; border-radius: 8px;
            padding: 0.6em 1em; font-size: 15px; font-weight: 600;
            width: 100%;
            margin-top: 10px;
            transition: background-color 0.2s;
        }
        div.stDownloadButton > button:hover {
            background-color: #0056b3;
        }
        
        /* Centering the logo image specifically */
        .logo-container {
            text-align: center;
        }

    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Logo + Subtitle (stacked, centered, no cropping)
# ====================================================
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("revolt_logo.png"):
    st.image("revolt_logo.png", width=120)  # slightly smaller for modern feel
else:
    st.write("⚠️ Add revolt_logo.png to repo root")
st.markdown('</div>', unsafe_allow_html=True)


st.markdown(
    """
    <h1 style="text-align: center; margin-top: 15px; font-weight: 700; color: #333; font-size: 32px;">
        Data Processor for AI
    </h1>
    <p style="text-align: center; color: #666; margin-bottom: 30px;">
        Clean, filter, and prepare your data for machine learning models.
    </p>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Upload + Processing
# ====================================================
uploaded_file = st.file_uploader(
    "Upload Excel/CSV", 
    type=["xlsx", "xls", "csv"], 
    help="Limit 300MB per file: XLSX, XLS, CSV" # Added the limit text to the file_uploader for clarity
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
        
    # Center the processing button
    col_button = st.columns([1, 1, 1])[1] # Use the middle column for centering

    if col_button.button("🚀 Run Processing"):
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
            try:
                # Need to check if cleaned_output exists and is a valid Excel file
                cleaned_df = pd.ExcelFile(cleaned_output)
                total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
            except:
                total_rows = 0 # Handle case where the output file might not be created on error
            
            try:
                orig_df = pd.ExcelFile(input_path)
                orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
            except:
                orig_rows = 0
                
            removed_rows = orig_rows - total_rows
            
            total_blocklist = len(load_blocklist()) # Load the latest count after processing

            # ================================
            # Summary Card (Cleaned Look)
            # ================================
            st.markdown(
                f"""
                <div class="result-box">
                <h4>✅ Processing Complete</h4>
                
                <div style="display: flex; justify-content: space-between; gap: 20px;">
                    <div style="flex: 1;">
                        <p style="font-size: 16px; margin-bottom: 5px;"><b>Processed Rows</b></p>
                        <h2 style="color: #e30613; margin-top: 0;">{orig_rows}</h2>
                    </div>
                    <div style="flex: 1;">
                        <p style="font-size: 16px; margin-bottom: 5px;"><b>Cleaned Rows</b></p>
                        <h2 style="color: #008000; margin-top: 0;">{total_rows}</h2>
                    </div>
                    <div style="flex: 1;">
                        <p style="font-size: 16px; margin-bottom: 5px;"><b>New Blocklisted</b></p>
                        <h2 style="color: #ffaa00; margin-top: 0;">+{result['new_numbers']}</h2>
                    </div>
                </div>
                
                <hr style="margin-top: 20px; margin-bottom: 10px; border-color: #eee;">
                
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
            # Downloads Section (Using st.columns)
            # ================================
            st.markdown("---")
            st.markdown('<h4 style="text-align: center; margin-top: 30px; margin-bottom: 20px;">Download Results</h4>', unsafe_allow_html=True)
            
            # Create a 3-column layout for the downloads
            col1, col2, col3 = st.columns([1, 1, 1])
            
            # Cleaned file
            with col1:
                st.markdown('<div style="text-align: center;"><b>Cleaned Data</b></div>', unsafe_allow_html=True)
                if os.path.exists("cleaned_logo.png"):
                    st.image("cleaned_logo.png", width=50)
                with open(cleaned_output, "rb") as f:
                    st.download_button("⬇️ Download Cleaned", f, file_name=f"cleaned_{timestamp}.xlsx")

            # Flagged log
            with col2:
                st.markdown('<div style="text-align: center;"><b>Flagged Log</b></div>', unsafe_allow_html=True)
                if os.path.exists("flagged_logo.png"):
                    st.image("flagged_logo.png", width=50)
                with open(flagged_log, "rb") as f:
                    st.download_button("⬇️ Download Flagged", f, file_name=f"flagged_{timestamp}.txt")

            # Blocklist
            with col3:
                st.markdown('<div style="text-align: center;"><b>Updated Blocklist</b></div>', unsafe_allow_html=True)
                if os.path.exists("blocklist_logo.png"):
                    st.image("blocklist_logo.png", width=50)
                with open(blocklist_file, "rb") as f:
                    # Note: We download the potentially updated local copy
                    st.download_button("⬇️ Download Blocklist", f, file_name=f"blocklist_{timestamp}.csv")
            
            st.markdown("---")
            
            # GitHub Commit + Cleanup
            commit_blocklist_to_github()
            cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])
