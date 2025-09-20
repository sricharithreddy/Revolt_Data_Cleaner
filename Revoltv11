import pandas as pd
import re
import os
import json
import argparse
from typing import List, Dict, Optional

def split_camel_case(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    # Only attempt camel-case splitting if the string contains lowercase letters
    # (avoids splitting ALLCAPS like "RAFEEK" into single letters).
    if any(c.islower() for c in name):
        parts = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name)
        return " ".join(parts.split())
    # Otherwise return the name as-is (we'll normalize capitalization later)
    return name
def is_sensible_name(name: str, original_name: str, row_index: Optional[int], logs: List[Dict]) -> bool:
    """
    Determine if a cleaned name looks sensible. Blacklist matching is applied only when the
    entire cleaned name equals a blacklist word/phrase (whole-name match), not when a blacklist
    entry appears as a token inside a multi-word name.
    """
    if not name or not isinstance(name, str):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": name, "reason": "empty_or_invalid_input"})
        return False
    lower_name = name.lower().strip()

    # Blacklist of problematic tokens/phrases (match whole name only)
    blacklist = [
        "joker", "k", "ccc", "aaa", "busy", "king", "spam", "failureboys",
        "radhe radhe", "jai mata di", "jaisairam", "shubh din",
        "emergency enquiry", "spam callers", "black world",
        "indian soldiers lover", "miss youu guruji", "sss", "adc",
        "dsp", "ettlement", "ww wmeresathi", "bsnl fiber", "null",
        "lets learn", "typing", "always be positive", "it doesnt matter",
        "next", "rss", "vvv", "ggg", "kk", "ok",
        # placeholders
        "lead", "test", "dummy", "na", "abc", "hotel"
    ]

    # Only flag when the full cleaned name equals a blacklist entry (or phrase)
    for word in blacklist:
        w = word.lower().strip()
        if not w:
            continue
        if lower_name == w:
            logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": name, "reason": f"blacklist_match:{w}"})
            return False

    # Other sanity checks
    if len(lower_name) < 2:
        logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": name, "reason": "too_short"})
        return False
    if re.match(r'^\d+$', lower_name):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": name, "reason": "numeric"})
        return False
    # Ensure likely a name (has vowel or apostrophe)
    if not re.search(r'[aeiou]', lower_name):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": name, "reason": "no_vowels"})
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
    try:
        if pd.isna(name) or not isinstance(name, str) or not name.strip():
            logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": "", "reason": "empty_or_invalid_input"})
            return ""
    except Exception:
        # If name is not a string or pandas NA
        if not name:
            logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": "", "reason": "empty_or_invalid_input"})
            return ""
    name = name.strip()

    # Remove common bike model mentions (case-insensitive)
    bike_models_to_remove = ["RV1", "RV400", "RV400BRZ", "RV1+", "RV BLAZEX", "RV-400", "RV 400", "RV BLAZE", "RV BLAZE X"]
    pattern = re.compile("(" + "|".join(re.escape(word) for word in bike_models_to_remove) + ")", re.IGNORECASE)
    name = pattern.sub("", name).strip()

    # Remove hyphens/dashes completely (replace with blank)
    name = re.sub(r"[-\u2013\u2014]", "", name)

    # Remove underscores, dots, numbers and common symbols, but keep spaces and apostrophes
    name = re.sub(r"[_\.0-9!@#$%^&*()+=?/,<>;:\"\\|{}\[\]~`]", "", name)

    # Normalize unicode spaces (NBSP, thin space, zero-width etc.) and remove zero-width joiners
    name = name.replace('\u00A0', ' ')
    name = re.sub(r'[\u2000-\u200B\u202F\u205F\uFEFF]', ' ', name)
    name = name.replace('\u200D', '')
    # Collapse multiple whitespace to single space
    name = re.sub(r'\s+', ' ', name).strip()

    # Detect and fix spaced-out single letters e.g., "S U R A J" -> "Suraj"
    if re.match(r'^(?:[A-Za-z]\s+){2,}[A-Za-z]$', name.strip()):
        collapsed = re.sub(r'\s+', '', name)
        collapsed = collapsed.capitalize()
        return collapsed

    # Extra heuristic: if most tokens are single letters, join them
    tokens = re.split(r'\s+', name.strip())
    cleaned_tokens = [re.sub(r'[^A-Za-z]', '', t) for t in tokens]
    single_letter_count = sum(1 for t in cleaned_tokens if len(t) == 1)
    if len(cleaned_tokens) >= 3 and single_letter_count >= max(2, int(len(cleaned_tokens) * 0.5)):
        letters_only = ''.join([t for t in cleaned_tokens if len(t) == 1])
        if len(letters_only) >= 3:
            return letters_only.capitalize()

    # Additional heuristic: if the string is mostly letters separated by spaces (including some separators), collapse
    letters_only = re.sub(r'[^A-Za-z]', '', name)
    space_count = len(re.findall(r'\s', name))
    if letters_only and len(letters_only) >= 3 and space_count >= max(1, len(letters_only) - 1):
        return letters_only.capitalize()

    # Normalize spaces again
    name = re.sub(r'\s+', ' ', name).strip()

    # If after removals it's purely numeric, flag
    if re.match(r'^\d+$', name.strip()):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": "", "reason": "purely_numeric_after_removal"})
        return ""

    # Keep only letters, spaces, apostrophes
    cleaned = re.sub(r"[^a-zA-Z\s']", "", name).strip()

    if not cleaned:
        logs.append({"index": row_index if row_index is not None else "", "original": original_name, "cleaned": "", "reason": "no_valid_characters_after_cleaning"})
        return ""

    # Split camel case heuristics and normalize capitalization
    cleaned = split_camel_case(cleaned)

    # If original had no spaces and looked like camel-case boundary (e.g., 'RafeeK'),
    # joining the trailing single-letter token usually produces the intended name 'Rafeek'.
    try:
        orig = str(original_name) if original_name is not None else ""
        # detect a lowercase->Uppercase boundary in original (heuristic for camel-case like 'RafeeK')
        has_lower_upper = bool(re.search(r'[a-z][A-Z]', orig))
        had_space_in_original = bool(re.search(r'\s', orig))
        tokens_after_split = cleaned.split()
        if has_lower_upper and not had_space_in_original and len(tokens_after_split) >= 2 and len(tokens_after_split[-1]) == 1:
            # join all tokens into a single word and capitalize
            joined = ''.join(tokens_after_split)
            cleaned = joined.capitalize()
    except Exception:
        pass
    cleaned = ' '.join(word.capitalize() for word in cleaned.split())

    if not is_sensible_name(cleaned, original_name, row_index, logs):
        return ""

    return cleaned

def clean_mobile_number(raw_mobile: str, row_index: Optional[int], logs: List[Dict]) -> str:
    if pd.isna(raw_mobile):
        logs.append({"index": row_index if row_index is not None else "", "original": raw_mobile, "cleaned_mobile": "", "reason": "mobile_is_na"})
        return ""
    s = str(raw_mobile).strip()
    # Remove leading '+' or '00' country codes and optional separator
    s = re.sub(r'^(\+|00)?\d{1,3}[-\s]?', '', s)
    digits = re.sub(r'\D', '', s)
    if len(digits) < 10:
        logs.append({"index": row_index if row_index is not None else "", "original": raw_mobile, "cleaned_mobile": "", "reason": f"too_short_digits:{digits}"})
        return ""
    cleaned = digits[-10:]
    return cleaned

def process_file(input_file_path: str, output_file_path: str, flagged_log_path: str = "flagged_names.txt"):
    # Validate input
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    # Prepare logs list
    logs: List[Dict] = []

    # Default rename rules (normalized keys: lower + no spaces/underscores)
    rename_rules = {
        "mobilenumber": "Mobile Number",
        "buyername": "Customer Name",
        "testridedateandtimeactual": "trscheduleactual"
    }
    # Merge any user-provided rev names from environment variable (JSON expected)
    env_rules = os.getenv("REVOLT_RENAMES")
    if env_rules:
        try:
            extra = json.loads(env_rules)
            # Normalize keys
            for k, v in extra.items():
                kn = k.strip().lower().replace(" ", "").replace("_", "")
                if kn:
                    rename_rules[kn] = v
        except Exception:
            # Ignore errors parsing env var
            pass

    # Read input file (support multiple sheets)
    if input_file_path.lower().endswith(('.xlsx', '.xls')):
        all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    elif input_file_path.lower().endswith('.csv'):
        all_sheets = {"Sheet1": pd.read_csv(input_file_path)}
    else:
        raise ValueError("Unsupported file format. Provide .csv, .xls or .xlsx")

    cleaned_sheets = {}

    for sheet_name, df in all_sheets.items():
        # Opportunity id rename if present (keep backward compatibility)
        if 'opportunityid' in df.columns:
            df.rename(columns={'opportunityid': 'opportunity_id'}, inplace=True)

        # Apply merged rename rules: find matching columns by normalized name
        # Build normalized columns map: normalized -> actual column name
        normalized_cols = {re.sub(r'[\s_]', '', col).lower(): col for col in df.columns}
        df_renamed = {}
        for norm_key, new_name in rename_rules.items():
            if norm_key in normalized_cols:
                df_renamed[normalized_cols[norm_key]] = new_name
        if df_renamed:
            df.rename(columns=df_renamed, inplace=True)
            # Log the renames
            for old_col, new_col in df_renamed.items():
                logs.append({"index": "", "original": old_col, "cleaned": new_col, "reason": "column_renamed"})

        # Format trcompleteddate to "21st September" style (no year)
        if 'trcompleteddate' in df.columns:
            df['trcompleteddate_parsed'] = pd.to_datetime(df['trcompleteddate'], errors='coerce')
            def format_date(dt):
                if pd.isna(dt):
                    return ""
                return f"{add_ordinal_suffix(dt.day)} {dt.strftime('%B')}"
            df['trcompleteddate'] = df['trcompleteddate_parsed'].apply(format_date).astype(str)
            df.drop(columns=['trcompleteddate_parsed'], inplace=True)

        # Format trscheduleactual similarly if present
        if 'trscheduleactual' in df.columns:
            df['trscheduleactual_parsed'] = pd.to_datetime(df['trscheduleactual'], errors='coerce')
            def format_schedule(dt):
                if pd.isna(dt):
                    return ""
                return f"{add_ordinal_suffix(dt.day)} {dt.strftime('%B')}"
            df['trscheduleactual'] = df['trscheduleactual_parsed'].apply(format_schedule).astype(str)
            df.drop(columns=['trscheduleactual_parsed'], inplace=True)

        # Mobile cleanup - find candidate columns
        mobile_col_candidates = [col for col in df.columns if col.lower().replace(' ', '') in ('mobilenumber', 'mobile', 'mobile_no', 'mobileno', 'contactnumber')]
        if mobile_col_candidates:
            mobile_col = mobile_col_candidates[0]
            df[mobile_col] = [clean_mobile_number(raw, idx, logs) for idx, raw in df[mobile_col].items()]

        # Name cleanup - find candidate columns
        name_col_candidates = [col for col in df.columns if col.lower().replace(' ', '') in ('customername', 'customer', 'buyername', 'name')]
        if name_col_candidates:
            name_col = name_col_candidates[0]
            df[name_col] = [clean_customer_name(raw, idx, logs) for idx, raw in df[name_col].items()]

        cleaned_sheets[sheet_name] = df

    # Save cleaned sheets to Excel (with fallback to CSV)
    try:
        with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
            for sheet_name, df in cleaned_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        fallback_csv = os.path.splitext(output_file_path)[0] + ".csv"
        pd.concat(cleaned_sheets.values(), ignore_index=True).to_csv(fallback_csv, index=False)
        print(f"Excel save failed ({e}). Saved CSV to {fallback_csv}")

    # Write flagged log
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
