import pandas as pd
import re
import os
from typing import List, Dict, Optional
from datetime import datetime

# ====================================================
# Helper Functions
# ====================================================
def split_camel_case(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    if any(c.islower() for c in name):
        parts = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name)
        return " ".join(parts.split())
    return name

def looks_like_date(val):
    try:
        dt = pd.to_datetime(val, errors="coerce", dayfirst=True)
        return pd.notna(dt)
    except Exception:
        return False

def format_date_column(df, col):
    formatted = []
    for val in df[col]:
        try:
            dt = pd.to_datetime(val, errors="coerce", dayfirst=True)
            if pd.notna(dt):
                if os.name == "nt":
                    formatted.append(dt.strftime("%#d %B"))
                else:
                    formatted.append(dt.strftime("%-d %B"))
            else:
                formatted.append(str(val))
        except Exception:
            formatted.append(str(val))
    df[col] = formatted
    return df

def is_sensible_name(name: str, original_name: str, row_index: Optional[int], logs: List[Dict]) -> bool:
    if not name or not isinstance(name, str):
        return False
    lower_name = name.lower().strip()
    if len(lower_name) < 2 or re.match(r'^\d+$', lower_name):
        return False
    if not re.search(r'[aeiou]', lower_name):
        return False
    return True

def clean_customer_name(name: str, row_index: Optional[int], logs: List[Dict]) -> str:
    original_name = name
    try:
        if pd.isna(name) or not isinstance(name, str) or not name.strip():
            return ""
    except Exception:
        return ""
    name = name.strip()
    name = re.sub(r"[-_.0-9!@#$%^&*()+=?/,<>;:\"\\|{}\[\]~`]", "", name)
    name = re.sub(r'\s+', ' ', name).strip()
    cleaned = re.sub(r"[^a-zA-Z\s']", "", name).strip()
    if not cleaned:
        return ""
    cleaned = split_camel_case(cleaned)
    cleaned = ' '.join(word.capitalize() for word in cleaned.split())
    if not is_sensible_name(cleaned, original_name, row_index, logs):
        return ""
    return cleaned

def clean_mobile_number(raw_mobile: str, row_index: Optional[int], logs: List[Dict]) -> str:
    if pd.isna(raw_mobile):
        return ""
    s = str(raw_mobile).strip()
    s = re.sub(r'^(\+|00)?\d{1,3}[-\s]?', '', s)
    digits = re.sub(r'\D', '', s)
    if len(digits) < 10:
        return ""
    return digits[-10:]

# ====================================================
# Main Processing Function
# ====================================================
def process_file(input_file_path: str):
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    today_str = datetime.today().strftime("%d %b").lstrip("0")
    all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    template_cols = ['hub', 'model', 'customer_name', 'mobile_number', 'opportunity_id', 'trscheduleactual']
    outputs = {}

    for sheet_name, df in all_sheets.items():
        # Clean name and mobile
        for col in df.columns:
            if col.lower().strip() in ['customername', 'customer', 'buyername', 'name']:
                df[col] = [clean_customer_name(v, i, []) for i, v in df[col].items()]
            if col.lower().strip() in ['mobile', 'mobilenumber', 'contactnumber', 'mobile_no']:
                df[col] = [clean_mobile_number(v, i, []) for i, v in df[col].items()]

        # For Feedback sheet, replace trscheduleactual with trcompleteddate
        if sheet_name.strip() == "TR_Completed_Y-5_to_Y" and 'trcompleteddate' in df.columns:
            df['trscheduleactual'] = df['trcompleteddate']

        # Reformat to match Calls structure
        for col in template_cols:
            if col not in df.columns:
                df[col] = ""
        df = df[template_cols]

        # Save each as per requirement
        if sheet_name.strip() == "Upcoming_TR_Today_to_Today+3":
            reminder_file = f"Revolt TD Reminder {today_str}.xlsx"
            with pd.ExcelWriter(reminder_file, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="Calls", index=False)
            outputs["reminder"] = reminder_file

        elif sheet_name.strip() == "TR_Completed_Y-5_to_Y":
            feedback_file = f"Revolt TD Feedback {today_str}.xlsx"
            with pd.ExcelWriter(feedback_file, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="Calls", index=False)
            outputs["feedback"] = feedback_file

    return outputs
