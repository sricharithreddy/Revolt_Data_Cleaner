import pandas as pd
import re
import os
from typing import List, Dict, Optional
from datetime import datetime

# ====================================================
# Helper Functions (kept from original, preserved behavior)
# ====================================================
def split_camel_case(name: str) -> str:
    if not name or not isinstance(name, str):
        return ""
    if any(c.islower() for c in name):
        parts = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name)
        return " ".join(parts.split())
    return name


def looks_like_date(val):
    """Check if a value looks like a date."""
    try:
        dt = pd.to_datetime(val, errors="coerce", dayfirst=True)
        return pd.notna(dt)
    except Exception:
        return False


def format_date_column(df, col):
    """Format detected date columns into '7 October' style strings."""
    formatted = []
    for val in df[col]:
        try:
            dt = pd.to_datetime(val, errors="coerce", dayfirst=True)
            if pd.notna(dt):
                if os.name == "nt":
                    formatted.append(dt.strftime("%#d %B"))  # Windows
                else:
                    formatted.append(dt.strftime("%-d %B"))  # Linux/Mac
            else:
                formatted.append(str(val))
        except Exception:
            formatted.append(str(val))
    df[col] = formatted
    return df


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

    if cleaned != original_name:
        logs.append({"index": row_index, "original": original_name, "cleaned": cleaned, "reason": "name_cleaned"})

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
    if cleaned != str(raw_mobile):
        logs.append({"index": row_index, "original": raw_mobile, "cleaned_mobile": cleaned, "reason": "mobile_cleaned"})
    return cleaned


# ====================================================
# Blocklist Support (with deduplication)
# ====================================================
def load_blocklist(file_path="seen_feedback_mobiles.csv"):
    try:
        df = pd.read_csv(file_path, dtype=str, header=None)
    except Exception:
        return pd.DataFrame(columns=["Mobile", "DateAdded"])
    
    if df.shape[1] == 1:
        df.columns = ["Mobile"]
        df["DateAdded"] = datetime.today().strftime("%Y-%m-%d")
        df.to_csv(file_path, index=False)
    else:
        df.columns = ["Mobile", "DateAdded"]

    # Deduplicate blocklist each time it’s loaded
    df.drop_duplicates(subset=["Mobile"], keep="first", inplace=True)
    df.to_csv(file_path, index=False)
    return df


# ====================================================
# Main Processing Function (preserves original behavior + dual exports)
# ====================================================
def process_file(
    input_file_path: str,
    flagged_log_path: str = "flagged_names.txt",
    apply_blocklist: bool = True,
    cutoff_date: Optional[datetime] = None
):
    """
    Processes input file, applies cleaning and blocklist, and generates two formatted outputs:
      - Revolt TD Reminder {date}.xlsx  (from sheet Upcoming_TR_Today_to_Today+3)
      - Revolt TD Feedback {date}.xlsx  (from sheet TR_Completed_Y-5_to_Y, using trcompleteddate -> trscheduleactual)

    Returns a dict with summary counts and paths to generated files (if created).
    """
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    logs: List[Dict] = []

    # Read input
    if input_file_path.lower().endswith(('.xlsx', '.xls')):
        all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    elif input_file_path.lower().endswith('.csv'):
        all_sheets = {"Sheet1": pd.read_csv(input_file_path)}
    else:
        raise ValueError("Unsupported file format")

    cleaned_sheets = {}
    new_numbers = 0
    blocklist_file = "seen_feedback_mobiles.csv"
    outputs = {"reminder": None, "feedback": None}

    # Standard Calls template columns (exact spelling)
    template_cols = ['hub', 'model', 'customer_name', 'mobile_number', 'opportunity_id', 'trscheduleactual']

    for sheet_name, df in all_sheets.items():
        # ✅ Rename 'opportunityid' to 'opportunity_id' if present
        df.rename(columns=lambda x: "opportunity_id" if isinstance(x, str) and x.strip().lower() == "opportunityid" else x, inplace=True)

        # Mobile cleanup
        mobile_candidates = [col for col in df.columns if isinstance(col, str) and col.lower().replace(' ', '') in (
            'mobilenumber', 'mobile', 'mobile_no', 'mobileno', 'contactnumber'
        )]
        mobile_col = mobile_candidates[0] if mobile_candidates else None

        if mobile_col:
            df[mobile_col] = [clean_mobile_number(raw, idx, logs) for idx, raw in df[mobile_col].items()]

        # Name cleanup
        name_candidates = [col for col in df.columns if isinstance(col, str) and col.lower().replace(' ', '') in (
            'customername', 'customer', 'buyername', 'name'
        )]
        if name_candidates:
            name_col = name_candidates[0]
            df[name_col] = [clean_customer_name(raw, idx, logs) for idx, raw in df[name_col].items()]

        # Date formatting detection
        date_candidates = [col for col in df.columns if isinstance(col, str) and "date" in col.lower()]
        for col in df.columns:
            sample_vals = df[col].dropna().astype(str).head(10)
            if any(looks_like_date(v) for v in sample_vals):
                if col not in date_candidates:
                    date_candidates.append(col)
        for dcol in date_candidates:
            try:
                df = format_date_column(df, dcol)
            except Exception:
                pass

        # ====================================================
        # Blocklist filtering (applies to both sheets equally)
        # ====================================================
        if apply_blocklist and mobile_col:
            blocklist_df = load_blocklist(blocklist_file)
            blocklist_df["DateAdded"] = pd.to_datetime(blocklist_df["DateAdded"], errors="coerce")

            if cutoff_date:
                cutoff_dt = pd.to_datetime(cutoff_date)
                blocklist_df = blocklist_df[blocklist_df["DateAdded"] <= cutoff_dt]

            existing_mobiles = set(blocklist_df["Mobile"].astype(str))
            flagged = df[df[mobile_col].astype(str).isin(existing_mobiles)]

            # Log blocklist matches
            for idx, row in flagged.iterrows():
                logs.append({"index": idx, "original": row[mobile_col], "cleaned": "", "reason": "blocklist_match"})

            # Save flagged list
            flagged[mobile_col].to_csv(flagged_log_path, index=False, header=False)

            # Remove blocked numbers from main DataFrame
            df = df[~df[mobile_col].astype(str).isin(existing_mobiles)]

            # Identify *new* mobile numbers not already in blocklist
            new_mobiles = set(df[mobile_col].astype(str)) - existing_mobiles
            new_numbers = len(new_mobiles)

            # Append only new numbers to blocklist file
            if new_numbers > 0:
                new_entries = pd.DataFrame({
                    "Mobile": list(new_mobiles),
                    "DateAdded": datetime.today().strftime("%Y-%m-%d")
                })
                new_entries.to_csv(blocklist_file, mode="a", index=False, header=False)

        cleaned_sheets[sheet_name] = df

    # ====================================================
    # Create the two required outputs using Calls structure
    # ====================================================
    today_str = datetime.today().strftime("%d %b").lstrip("0")

    # Helper to coerce and align a dataframe to template columns
    def align_to_template(df: pd.DataFrame, template_cols: List[str]) -> pd.DataFrame:
        # If mobile column present under other name, rename to mobile_number
        possible_mobile_cols = [c for c in df.columns if isinstance(c, str) and c.lower().replace(' ', '') in ('mobilenumber', 'mobile', 'mobile_no', 'mobileno', 'contactnumber')]
        if possible_mobile_cols:
            if 'mobile_number' not in df.columns:
                df.rename(columns={possible_mobile_cols[0]: 'mobile_number'}, inplace=True)
        # If name column present under other name, rename to customer_name
        possible_name_cols = [c for c in df.columns if isinstance(c, str) and c.lower().replace(' ', '') in ('customername','customer','buyername','name')]
        if possible_name_cols:
            if 'customer_name' not in df.columns:
                df.rename(columns={possible_name_cols[0]: 'customer_name'}, inplace=True)
        # If opportunity_id exists as opportunity_id already ensured earlier
        # Ensure all template columns exist
        for col in template_cols:
            if col not in df.columns:
                df[col] = ""
        # Keep only template columns in the exact order
        return df[template_cols]

    for sheet_name, df in cleaned_sheets.items():
        sname = sheet_name.strip()

        # For Feedback sheet, override trscheduleactual with trcompleteddate if present
        if sname == "TR_Completed_Y-5_to_Y":
            if 'trcompleteddate' in df.columns:
                df['trscheduleactual'] = df['trcompleteddate']
            # else keep whatever trscheduleactual is (or blank)

        # Align columns
        aligned = align_to_template(df.copy(), template_cols)

        # Save only if it's one of the two target sheets
        if sname == "Upcoming_TR_Today_to_Today+3":
            reminder_file = f"Revolt TD Reminder {today_str}.xlsx"
            with pd.ExcelWriter(reminder_file, engine="xlsxwriter") as writer:
                aligned.to_excel(writer, sheet_name="Calls", index=False)
            outputs["reminder"] = os.path.abspath(reminder_file)

        elif sname == "TR_Completed_Y-5_to_Y":
            feedback_file = f"Revolt TD Feedback {today_str}.xlsx"
            with pd.ExcelWriter(feedback_file, engine="xlsxwriter") as writer:
                aligned.to_excel(writer, sheet_name="Calls", index=False)
            outputs["feedback"] = os.path.abspath(feedback_file)

    # Save flagged log
    with open(flagged_log_path, "w", encoding="utf-8") as f:
        f.write("index,original,cleaned,reason\n")
        for entry in logs:
            idx = entry.get("index", "")
            orig = str(entry.get("original", "")).replace('\n', ' ').replace(',', ' ')
            cleaned = entry.get("cleaned", entry.get("cleaned_mobile", ""))
            reason = entry.get("reason", "")
            f.write(f"{idx},{orig},{cleaned},{reason}\n")

    # Summary counts
    name_fixes = sum(1 for log in logs if log.get("reason") == "name_cleaned")
    mobile_fixes = sum(1 for log in logs if log.get("reason") == "mobile_cleaned")
    invalid_cases = sum(1 for log in logs if log.get("reason") in (
        "empty_or_invalid_input", "numeric", "no_vowels", "too_short",
        "purely_numeric_after_removal", "no_valid_characters_after_cleaning",
        "mobile_is_na", "too_short_digits", "blocklist_match"
    ))

    return {
        "new_numbers": new_numbers,
        "name_fixes": name_fixes,
        "mobile_fixes": mobile_fixes,
        "invalid_cases": invalid_cases,
        "outputs": outputs,
        "flagged_log": os.path.abspath(flagged_log_path)
    }
