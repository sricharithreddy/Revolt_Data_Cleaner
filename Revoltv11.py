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

def is_sensible_name(name: str, original_name: str, row_index: Optional[int], logs: List[Dict]) -> bool:
    if not name or not isinstance(name, str):
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "empty_or_invalid_input"})
        return False

    lower_name = name.lower().strip()
    blacklist = [
        "joker","k","ccc","aaa","busy","king","spam","failureboys",
        "radhe radhe","jai mata di","jaisairam","shubh din",
        "emergency enquiry","spam callers","black world",
        "indian soldiers lover","miss youu guruji","sss","adc",
        "dsp","ettlement","ww wmeresathi","bsnl fiber","null",
        "lets learn","typing","always be positive","it doesnt matter",
        "next","rss","vvv","ggg","kk","ok","lead","test","dummy","na","abc","hotel"
    ]
    for word in blacklist:
        if lower_name == word:
            logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": f"blacklist_match:{word}"})
            return False

    if len(lower_name) < 2:
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "too_short"})
        return False
    if re.match(r'^\d+$', lower_name):
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "numeric"})
        return False
    if not re.search(r'[aeiou]', lower_name):
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "no_vowels"})
        return False
    return True

def clean_customer_name(name: str, row_index: Optional[int], logs: List[Dict]) -> str:
    original_name = name
    try:
        if pd.isna(name) or not isinstance(name, str) or not name.strip():
            logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "empty_or_invalid_input"})
            return ""
    except Exception:
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "empty_or_invalid_input"})
        return ""

    name = name.strip()

    # Remove bike models
    bike_models_to_remove = ["RV1","RV400","RV400BRZ","RV1+","RV BLAZEX","RV-400","RV 400","RV BLAZE","RV BLAZE X"]
    pattern = re.compile("(" + "|".join(re.escape(word) for word in bike_models_to_remove) + ")", re.IGNORECASE)
    name = pattern.sub("", name).strip()

    # Clean symbols/numbers
    name = re.sub(r"[-\u2013\u2014]", "", name)
    name = re.sub(r"[_\.0-9!@#$%^&*()+=?/,<>;:\"\\|{}\[\]~`]", "", name)
    name = re.sub(r'\s+', ' ', name).strip()

    if re.match(r'^\d+$', name.strip()):
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "purely_numeric_after_removal"})
        return ""

    cleaned = re.sub(r"[^a-zA-Z\s']", "", name).strip()
    if not cleaned:
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "no_valid_characters_after_cleaning"})
        return ""

    cleaned = split_camel_case(cleaned)
    cleaned = ' '.join(word.capitalize() for word in cleaned.split())

    if not is_sensible_name(cleaned, original_name, row_index, logs):
        return ""

    return cleaned

def clean_mobile_number(raw_mobile: str, row_index: Optional[int], logs: List[Dict]) -> str:
    if pd.isna(raw_mobile):
        logs.append({"index": row_index, "original": raw_mobile, "cleaned_mobile": "", "reason": "mobile_is_na"})
        return ""
    s = str(raw_mobile).strip()
    s = re.sub(r'^(\+|00)?\d{1,3}[-\s]?', '', s)  # remove country code
    digits = re.sub(r'\D', '', s)
    if len(digits) < 10:
        logs.append({"index": row_index, "original": raw_mobile, "cleaned_mobile": "", "reason": f"too_short_digits:{digits}"})
        return ""
    return digits[-10:]

# ====================================================
# Blocklist Support
# ====================================================
def load_blocklist(file_path="seen_feedback_mobiles.csv"):
    try:
        df = pd.read_csv(file_path, dtype=str, header=None)
    except Exception:
        return pd.DataFrame(columns=["Mobile","DateAdded"])

    # Upgrade old format (single column → add DateAdded)
    if df.shape[1] == 1:
        df.columns = ["Mobile"]
        df["DateAdded"] = datetime.today().strftime("%Y-%m-%d")
        df.to_csv(file_path, index=False)
    else:
        df.columns = ["Mobile","DateAdded"]

    return df

# ====================================================
# Main Processing Function
# ====================================================
def process_file(
    input_file_path: str,
    output_file_path: str,
    flagged_log_path: str = "flagged_names.txt",
    apply_blocklist: bool = True,
    cutoff_date: Optional[datetime] = None
):
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    logs: List[Dict] = []

    # Read input (multi-sheet excel or csv)
    if input_file_path.lower().endswith(('.xlsx','.xls')):
        all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    elif input_file_path.lower().endswith('.csv'):
        all_sheets = {"Sheet1": pd.read_csv(input_file_path)}
    else:
        raise ValueError("Unsupported file format")

    cleaned_sheets = {}
    new_numbers = 0
    blocklist_file = "seen_feedback_mobiles.csv"

    for sheet_name, df in all_sheets.items():
        # Detect mobile col
        mobile_candidates = [col for col in df.columns if col.lower().replace(' ','') in (
            'mobilenumber','mobile','mobile_no','mobileno','contactnumber'
        )]
        mobile_col = mobile_candidates[0] if mobile_candidates else None

        if mobile_col:
            df[mobile_col] = [clean_mobile_number(raw, idx, logs) for idx, raw in df[mobile_col].items()]

        # Detect name col
        name_candidates = [col for col in df.columns if col.lower().replace(' ','') in (
            'customername','customer','buyername','name'
        )]
        if name_candidates:
            name_col = name_candidates[0]
            df[name_col] = [clean_customer_name(raw, idx, logs) for idx, raw in df[name_col].items()]

        # Blocklist filtering
        if apply_blocklist and mobile_col:
            blocklist_df = load_blocklist(blocklist_file)
            blocklist_df["DateAdded"] = pd.to_datetime(blocklist_df["DateAdded"], errors="coerce")

            # Apply cutoff date
            if cutoff_date:
                cutoff_dt = pd.to_datetime(cutoff_date)
                blocklist_df = blocklist_df[blocklist_df["DateAdded"] <= cutoff_dt]

            blocklist = blocklist_df["Mobile"].astype(str).tolist()
            flagged = df[df[mobile_col].astype(str).isin(blocklist)]

            # Record blocklist matches in logs
            for idx, row in flagged.iterrows():
                logs.append({
                    "index": idx,
                    "original": row[mobile_col],
                    "cleaned": "",
                    "reason": "blocklist_match"
                })

            # Save flagged numbers separately
            flagged[mobile_col].to_csv(flagged_log_path, index=False, header=False)

            # Remove blocklisted rows
            df = df[~df[mobile_col].astype(str).isin(blocklist)]
            new_numbers = len(flagged)

            # Append new blocklist entries
            if new_numbers > 0:
                new_entries = pd.DataFrame({
                    "Mobile": flagged[mobile_col].astype(str).drop_duplicates(),
                    "DateAdded": datetime.today().strftime("%Y-%m-%d")
                })
                new_entries.to_csv(blocklist_file, mode="a", index=False, header=False)

        cleaned_sheets[sheet_name] = df

    # Save cleaned file
    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        for sheet_name, df in cleaned_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Save flagged log (all issues, incl. blocklist)
    with open(flagged_log_path, "w", encoding="utf-8") as f:
        f.write("index,original,cleaned,reason\n")
        for entry in logs:
            idx = entry.get("index","")
            orig = str(entry.get("original","")).replace('\n',' ').replace(',',' ')
            cleaned = entry.get("cleaned", entry.get("cleaned_mobile",""))
            reason = entry.get("reason","")
            f.write(f"{idx},{orig},{cleaned},{reason}\n")

    return {"new_numbers": new_numbers}
