import pandas as pd
import re
import os
import argparse
from typing import List, Dict, Optional

def split_camel_case(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    if name.isupper() and len(name) > 1 and ' ' not in name:
        parts = re.findall(r'[A-Z][^A-Z]*', name)
        if len(parts) > 1:
            return " ".join(parts)
        mid = len(name) // 2
        return name[:mid].capitalize() + " " + name[mid:].capitalize()
    parts = re.sub('([a-z0-9])([A-Z])', r'\1 \2', name)
    return " ".join(parts.split())

def is_sensible_name(name: str, original_name: str, row_index: Optional[int], logs: List[Dict]) -> bool:
    if not name or not isinstance(name, str):
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "empty_or_invalid_input"})
        return False
    lower_name = name.lower().strip()
    blacklist = [
        "joker", "k", "ccc", "aaa", "busy", "king", "spam", "failureboys",
        "radhe radhe", "jai mata di", "jaisairam", "shubh din",
        "emergency enquiry", "spam callers", "black world",
        "indian soldiers lover", "miss youu guruji", "sss", "adc",
        "dsp", "ettlement", "ww wmeresathi", "bsnl fiber", "null",
        "lets learn", "typing", "always be positive", "it doesnt matter",
        "next", "rss", "vvv", "ggg", "kk", "ok",
        # Added placeholders
        "lead", "test", "dummy", "na", "abc", "hotel"
    ]
    for word in blacklist:
        if re.search(r'\b' + re.escape(word) + r'\b', lower_name):
            logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": f"blacklist_match:{word}"})
            return False
    if len(lower_name) < 3:
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "too_short"})
        return False
    if re.match(r'^\d+$', lower_name):
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "numeric"})
        return False
    if not re.search(r'[aeiou]', lower_name):
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "no_vowels"})
        return False
    return True

def add_ordinal_suffix(day):
    try:
        day = int(day)
    except Exception:
        return ""
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"

def clean_customer_name(name: str, row_index: Optional[int], logs: List[Dict]) -> str:
    original_name = name
    if pd.isna(name) or not isinstance(name, str) or not name.strip():
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "empty_or_invalid_input"})
        return ""

    # Remove bike models
    bike_models_to_remove = ["RV1", "RV400", "RV400BRZ", "RV1+", "RV BLAZEX", "RV-400", "RV 400", "RV BLAZE", "RV BLAZE X"]
    pattern = re.compile("(" + "|".join(re.escape(word) for word in bike_models_to_remove) + ")", re.IGNORECASE)
    name = pattern.sub("", name)

    # Replace hyphens with space, then remove underscores, dots, numbers, symbols
    name = re.sub(r"[-\u2013\u2014]", "", name)
    name = re.sub(r"[_\.0-9!@#$%^&*()+=?/,<>;:\"\\|{}\[\]~`]", "", name)

# Normalize unicode spaces (NBSP, thin space, zero-width etc.) and remove zero-width joiners
    name = name.replace('\u00A0', ' ')
    name = re.sub(r'[\u2000-\u200B\u202F\u205F]', ' ', name)
    name = name.replace('\u200D', '')
    # Collapse multiple whitespace characters to a single ASCII space
    name = re.sub(r'\s+', ' ', name).strip()

    # Detect and fix spaced-out single letters (e.g., 'S U R A J' -> 'Suraj')
    # Also handles cases with non-breaking spaces or weird whitespace characters
    if re.match(r'^(?:[A-Za-z]\s+){2,}[A-Za-z]$', name.strip()):
        name = name.replace(' ', '')

    # Additional heuristic: if the tokenized name consists of single-letter tokens repeatedly (e.g., ['H','O','T','E','L']),
    # join them together.
    tokens = name.split()
    if len(tokens) >= 3 and all(len(t) == 1 and re.match(r'[A-Za-z]', t) for t in tokens):
        name = ''.join(tokens)
    # Normalize spaces
    name = re.sub(r"\s+", " ", name).strip()

    if re.match(r'^\d+$', name.strip()):
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "purely_numeric_after_removal"})
        return ""

    # Keep only letters, spaces, apostrophes
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
    s = re.sub(r'^(\+|00)?\d{1,3}[-\s]?', '', s)
    digits = re.sub(r'\D', '', s)
    if len(digits) < 10:
        logs.append({"index": row_index, "original": raw_mobile, "cleaned_mobile": "", "reason": f"too_short_digits:{digits}"})
        return ""
    cleaned = digits[-10:]
    return cleaned

def process_file(input_file_path: str, output_file_path: str, flagged_log_path: str = "flagged_names.txt"):
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    if input_file_path.lower().endswith(('.xlsx', '.xls')):
        all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    elif input_file_path.lower().endswith('.csv'):
        all_sheets = {"Sheet1": pd.read_csv(input_file_path)}
    else:
        raise ValueError("Unsupported file format. Provide .csv, .xls or .xlsx")
    logs: List[Dict] = []
    cleaned_sheets = {}
    for sheet_name, df in all_sheets.items():
        
        # Generalized renaming (case-insensitive, ignores spaces/underscores)
        rename_targets = {
            'mobilenumber': 'Mobile Number',
            'buyername': 'Customer Name',
            'testridedateandtimeactual': 'trscheduleactual'
        }
        normalized_cols = {re.sub(r'[\s_]', '', col).lower(): col for col in df.columns}
        for key, new_name in rename_targets.items():
            if key.lower() in normalized_cols:
                df.rename(columns={normalized_cols[key.lower()]: new_name}, inplace=True)


        if 'opportunityid' in df.columns:
            df.rename(columns={'opportunityid': 'opportunity_id'}, inplace=True)
        if 'trcompleteddate' in df.columns:
            df['trcompleteddate_parsed'] = pd.to_datetime(df['trcompleteddate'], errors='coerce')
            def format_date(dt):
                if pd.isna(dt):
                    return ""
                return f"{add_ordinal_suffix(dt.day)} {dt.strftime('%B')}"
            df['trcompleteddate'] = df['trcompleteddate_parsed'].apply(format_date).astype(str)
            df.drop(columns=['trcompleteddate_parsed'], inplace=True)
        # Also format 'trscheduleactual' similarly to 'trcompleteddate'
        if 'trscheduleactual' in df.columns:
            df['trscheduleactual_parsed'] = pd.to_datetime(df['trscheduleactual'], errors='coerce')
            def format_schedule(dt):
                if pd.isna(dt):
                    return ""
                return f"{add_ordinal_suffix(dt.day)} {dt.strftime('%B')}"
            df['trscheduleactual'] = df['trscheduleactual_parsed'].apply(format_schedule).astype(str)
            df.drop(columns=['trscheduleactual_parsed'], inplace=True)

        mobile_col_candidates = [col for col in df.columns if col.lower().replace(' ', '') in ('mobilenumber', 'mobile', 'mobile_no', 'mobileno', 'contactnumber')]
        if mobile_col_candidates:
            mobile_col = mobile_col_candidates[0]
            df[mobile_col] = [clean_mobile_number(raw, idx, logs) for idx, raw in df[mobile_col].items()]
        name_col_candidates = [col for col in df.columns if col.lower().replace(' ', '') in ('customername', 'customer', 'buyername', 'name')]
        if name_col_candidates:
            name_col = name_col_candidates[0]
            df[name_col] = [clean_customer_name(raw, idx, logs) for idx, raw in df[name_col].items()]
        cleaned_sheets[sheet_name] = df
    try:
        with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
            for sheet_name, df in cleaned_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        fallback_csv = os.path.splitext(output_file_path)[0] + ".csv"
        pd.concat(cleaned_sheets.values(), ignore_index=True).to_csv(fallback_csv, index=False)
        print(f"Excel save failed ({e}). Saved CSV to {fallback_csv}")
    try:
        with open(flagged_log_path, "w", encoding="utf-8") as f:
            f.write("index,original,cleaned,reason\n")
            for entry in logs:
                idx = entry.get("index", "")
                orig = str(entry.get("original", "")).replace('\n', ' ').replace(',', ' ')
                reason = entry.get("reason", "")
                cleaned = entry.get("cleaned", entry.get("cleaned_mobile", ""))
                f.write(f"{idx},{orig},{cleaned},{reason}\n")
    except Exception as e:
        print(f"Failed to write log file {flagged_log_path}: {e}")
    print(f"Processed file saved to: {output_file_path}")
    print(f"Flagged log saved to: {flagged_log_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean customer and mobile data in Excel/CSV files.")
    parser.add_argument("input", help="Path to input file (.csv, .xls, .xlsx)")
    parser.add_argument("output", help="Path to output cleaned file (Excel preferred)")
    parser.add_argument("--log", default="flagged_names.txt", help="Path to save flagged log file (default: flagged_names.txt)")
    args = parser.parse_args()
    process_file(args.input, args.output, args.log)
