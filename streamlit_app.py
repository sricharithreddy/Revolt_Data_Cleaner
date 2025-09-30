import streamlit as st
import base64

# ===============================
# Page Setup
# ===============================
st.set_page_config(
    page_title="Revolt Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ===============================
# Custom CSS
# ===============================
st.markdown(
    """
    <style>
        /* Page background */
        .main {
            background-color: #f5f6f8;
        }

        /* Center content */
        .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 30px;
        }

        /* Upload + results box */
        .card {
            background: #ffffff;
            padding: 30px 40px;
            border-radius: 14px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.08);
            max-width: 500px;
            width: 100%;
            text-align: center;
            margin-top: 20px;
        }

        /* CTA Button */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #e30613, #b0000d);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.7em 1.4em;
            font-size: 16px;
            font-weight: 600;
            transition: 0.3s;
            width: 100%;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(90deg, #b0000d, #e30613);
            transform: scale(1.01);
        }

        /* Download buttons inline */
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
            border: 1px solid #ccc;
            background: #fafafa;
            color: #333;
        }
        .downloads div.stDownloadButton button:hover {
            border: 1px solid #e30613;
            color: #e30613;
            background: #fff;
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

# ===============================
# Logo (Placeholder)
# ===============================
st.markdown(
    """
    <div style="display:flex;justify-content:center;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6e/Revolt_Motors_logo.png" width="140">
    </div>
    """,
    unsafe_allow_html=True
)

# ===============================
# Upload + Process Card
# ===============================
st.markdown('<div class="card">', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file is not None:
    if st.button("🚀 Run Cleaning"):
        # ===== Placeholder for backend logic =====
        st.success(
            """
            ✅ **Processed:** 10,000 rows  
            📤 **Cleaned File:** 9,200 rows  
            🚫 **Removed (blocklisted):** 800 rows  
            📋 **Blocklist Update:** +120 new numbers
            """
        )

        # Downloads section
        st.markdown('<div class="downloads">', unsafe_allow_html=True)
        st.download_button("⬇️ Cleaned File", "dummy content", file_name="cleaned.xlsx")
        st.download_button("⬇️ Flagged Log", "dummy content", file_name="flagged.txt")
        st.download_button("⬇️ Blocklist", "dummy content", file_name="blocklist.csv")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # close card
