import streamlit as st
import os
import tempfile
import pandas as pd
from datetime import datetime
import base64
import json
from streamlit_lottie import st_lottie
from Revoltv11 import process_file

# ------------------------
# Helper: Encode logo as base64
# ------------------------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

LOGO_PATH = "revolt_logo.png"
logo_html = ""
if os.path.exists(LOGO_PATH):
    logo_base64 = get_base64_of_bin_file(LOGO_PATH)
    # ✅ Larger logo + pulse animation
    logo_html = f'''
    <img src="data:image/png;base64,{logo_base64}" 
         width="180" 
         style="margin-right:15px; animation: pulse 2s infinite;">
    '''

# ------------------------
# Page Config
# ------------------------
st.set_page_config(
    page_title="Revolt Data Cleaner",
    page_icon="⚡",
    layout="centered"
)

# ------------------------
# Load Lottie Animation
# ------------------------
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

bike_anim = None
if os.path.exists("bike.json"):
    bike_anim = load_lottiefile("bike.json")

# ------------------------
# Custom CSS Styling
# ------------------------
st.markdown(""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        font-weight: 700 !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #e30613, #b0000d);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-size: 16px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #b0000d, #7a0009);
        transform: scale(1.02);
    }
    .stDownloadButton>button {
        border-radius: 8px;
        border: 1px solid #ddd;
        background-color: white;
        color: #333;
        font-weight: 500;
        padding: 0.5em 1em;
    }
    .stDownloadButton>button:hover {
        background-color: #f8f9fa;
        border-color: #e30613;
        color: #e30613;
    }
    .summary-card {
        padding: 20px;
        border-radius: 15px;
        background: #ffffff;
        border
