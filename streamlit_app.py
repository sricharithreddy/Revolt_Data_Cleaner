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

        subprocess.run(
            ["git", "config", "--global", "user.email", f"{user}@users.noreply.github.com"], check=True
        )
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
st.set_page_config(
    page_title="Revolt Data Processor",
    page_icon="⚡",
    layout="centered"
)

# ====================================================
# Custom Styling
# ====================================================
st.markdown(
    """
    <style>
    /* Modern CTA button */
    div.stButton > button:first-child {
        background-color: #e30613;
        color: white;
        border-radius: 25px;
        padding: 0.6em 1.5em;
        font-weight: 600;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.2);
    }
    div.stButton > button:first-child:hover {
        background-color: #b0000d;
        transform: scale(1.02);
        transition: 0.2s;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ====================================================
# Branding (Logo + Subtitle centered)
# ====================================================
logo_col = st.columns([1, 2, 1])[1]
with logo_col:
    if os.path.exists("revolt_logo.png"):
        st.image("revolt_logo.png", width=140)
    else:
        st.warning("⚠️ Revolt logo not found. Please add revolt_logo.png")

    st.markdown(
        "<h3 style='text-align:center; color:#e30613; font-weight:700;'>Data Processor for AI</h3>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ====================================================
# File Upload Section
# ====================================================
with st.container(border=True):
    st.subheader("📂 Upload Your File")
    uploaded_file = st.file_uploader(
        "Upload Excel/CSV", type=["xlsx", "xls", "csv"], label_visibility="collapsed"
    )

# ====================================================
# Processing Logic
# ====================================================
if uploaded_file is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = f"uploaded_{timestamp}.xlsx"
    cleaned_output = f"cleaned_{timestamp}.xlsx"
    flagged_log = f"flagged_{timestamp}.txt"
    blocklist_file = "seen_feedback_mobiles.csv"

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    if st.button("🚀 Run Processing", use_container_width=True):
        with st.spinner("⚡ Processing in progress... Please wait..."):
            result = process_file(input_path, cleaned_output, flagged_log)

            # ====================================================
            # Process Summary
            # ====================================================
            with st.container(border=True):
                st.subheader("📊 Process Summary")

                cleaned_df = pd.ExcelFile(cleaned_output)
                total_rows = sum(len(cleaned_df.parse(s)) for s in cleaned_df.sheet_names)
                orig_df = pd.ExcelFile(input_path)
                orig_rows = sum(len(orig_df.parse(s)) for s in orig_df.sheet_names)
                removed_rows = orig_rows - total_rows

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("✅ Processed", orig_rows)
                m2.metric("🧹 Cleaned", total_rows, delta=total_rows - orig_rows)
                m3.metric("⛔ Removed", removed_rows, delta=-removed_rows if removed_rows > 0 else None)
                m4.metric("📋 New Blocklist", result["new_numbers"], delta=result["new_numbers"])

                st.caption(f"📋 Total Blocklist Size: {len(load_blocklist())}")

            # ====================================================
            # Downloads Section
            # ====================================================
            with st.container(border=True):
                st.subheader("⬇️ Downloads")

                d1, d2, d3 = st.columns(3)

                with d1:
                    with open(cleaned_output, "rb") as f:
                        st.download_button(
                            "✅ Cleaned File",
                            f,
                            file_name=f"cleaned_{timestamp}.xlsx",
                            use_container_width=True
                        )

                with d2:
                    with open(flagged_log, "rb") as f:
                        st.download_button(
                            "⚠️ Flagged Log",
                            f,
                            file_name=f"flagged_{timestamp}.txt",
                            use_container_width=True
                        )

                with d3:
                    with open(blocklist_file, "rb") as f:
                        st.download_button(
                            "⛔ Blocklist",
                            f,
                            file_name=f"blocklist_{timestamp}.csv",
                            use_container_width=True
                        )

            # ====================================================
            # Blocklist Preview
            # ====================================================
            with st.container(border=True):
                with st.expander("📋 Preview Blocklist (last 20 numbers)", expanded=False):
                    try:
                        blocklist_df = pd.read_csv(blocklist_file, header=None, names=["Mobile Number"])
                        st.dataframe(blocklist_df.tail(20), use_container_width=True)
                    except Exception:
                        st.info("No blocklist data available.")

            # ====================================================
            # GitHub Commit + Cleanup
            # ====================================================
            with st.spinner("🔄 Syncing blocklist to GitHub..."):
                commit_blocklist_to_github()
            cleanup_old_files([input_path, cleaned_output, flagged_log, blocklist_file])

# ====================================================
# Footer
# ====================================================
st.markdown(
    "<hr><p style='text-align:center; color:gray; font-size:14px;'>⚡ Powered by Orbitel ⚡</p>",
    unsafe_allow_html=True
)
