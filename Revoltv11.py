import pandas as pd
import re
import os
from typing import List, Dict, Optional

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
    if lower_name in blacklist:
        logs.append({"index": row_index, "original": original_name, "cleaned": name, "reason": "blacklist_match"})
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
    if pd.isna(name) or not isinstance(name, str) or not name.strip():
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "empty_or_invalid_input"})
        return ""
    name = name.strip()
    bike_models_to_remove = ["RV1","RV400","RV400BRZ","RV1+","RV BLAZEX","RV-400","RV 400","RV BLAZE","RV BLAZE X"]
    pattern = re.compile("(" + "|".join(re.escape(w) for w in bike_models_to_remove) + ")", re.IGNORECASE)
    name = pattern.sub("", name).strip()
    name = re.sub(r"[-_\.0-9!@#$%^&*()+=?/,<>;:\"\\|{}\[\]~`]", "", name)
    name = re.sub(r'\s+', ' ', name).strip()
    if not name:
        logs.append({"index": row_index, "original": original_name, "cleaned": "", "reason": "no_valid_characters_after_cleaning"})
        return ""
    cleaned = split_camel_case(name)
    cleaned = ' '.join(w.capitalize() for w in cleaned.split())
    if not is_sensible_name(cleaned, original_name, row_index, logs):
        return ""
    return cleaned

def clean_mobile_number(raw_mobile: str, row_index: Optional[int], logs: List[Dict]) -> str:
    if pd.isna(raw_mobile):
        logs.append({"index": row_index, "original": raw_mobile, "cleaned_mobile": "", "reason": "mobile_is_na"})
        return ""
    digits = re.sub(r'\D','', str(raw_mobile).strip())
    if len(digits) == 10:
        return digits
    if len(digits) > 10:
        return digits[-10:]
    logs.append({"index": row_index, "original": raw_mobile, "cleaned_mobile": "", "reason": "invalid_length"})
    return ""

def process_file(input_file_path: str, output_file_path: str, flagged_log_path: str = "flagged_names.txt"):
    logs: List[Dict] = []

    # Column rename rules
    rename_rules = {
        "mobilenumber": "Mobile Number",
        "buyername": "Customer Name",
        "testridedateandtimeactual": "trscheduleactual"
    }

    # Load input
    if input_file_path.lower().endswith(('.xlsx','.xls')):
        all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    elif input_file_path.lower().endswith('.csv'):
        all_sheets = {"Sheet1": pd.read_csv(input_file_path)}
    else:
        raise ValueError("Unsupported format")

    # --------------------
    # Blocklist Seeding
    # --------------------
    blocklist_file = "seen_feedback_mobiles.csv"
    seen_set = set()
    seeded_count = 0
    if os.path.exists(blocklist_file):
        seen_df = pd.read_csv(blocklist_file)
        seen_set = set(str(x).strip() for x in seen_df['Mobile Number'] if str(x).strip())
    else:
        # Try seeding from Calling Data.xlsx if available
        if os.path.exists("Calling Data.xlsx"):
            try:
                calls_df = pd.read_excel("Calling Data.xlsx", sheet_name="Calls")
                if "mobile_number" in calls_df.columns:
                    mobiles = []
                    for m in calls_df["mobile_number"].dropna():
                        digits = re.sub(r"\D", "", str(m))
                        if len(digits) == 10:
                            mobiles.append(digits)
                        elif len(digits) > 10:
                            mobiles.append(digits[-10:])
                    seen_set = set(mobiles)
                    pd.Series(sorted(seen_set), name="Mobile Number").to_csv(blocklist_file, index=False)
                    seeded_count = len(seen_set)
            except Exception as e:
                print(f"Seeding blocklist failed: {e}")

    new_numbers = set()
    cleaned_sheets = {}

    # --------------------
    # Cleaning Loop
    # --------------------
    for sheet_name, df in all_sheets.items():
        df = df.rename(columns=lambda c: rename_rules.get(c.lower().strip(), c))
        if "Mobile Number" in df.columns:
            df["Mobile Number"] = [clean_mobile_number(val, idx, logs) for idx, val in df["Mobile Number"].items()]
            df = df[~df["Mobile Number"].isin(seen_set)]
        if "Customer Name" in df.columns:
            df["Customer Name"] = [clean_customer_name(val, idx, logs) for idx, val in df["Customer Name"].items()]
        if sheet_name.lower() == "tr_completed" and "Mobile Number" in df.columns:
            new_numbers.update([str(x).strip() for x in df["Mobile Number"] if str(x).strip()])
        cleaned_sheets[sheet_name] = df

    # --------------------
    # Update blocklist
    # --------------------
    if new_numbers:
        updated_numbers = sorted(seen_set.union(new_numbers))
        pd.Series(updated_numbers, name="Mobile Number").to_csv(blocklist_file, index=False)

    # Save cleaned Excel
    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        for sheet_name, df in cleaned_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Save flagged log
    with open(flagged_log_path, "w", encoding="utf-8") as f:
        f.write("index,original,cleaned,reason\n")
        for entry in logs:
            idx = entry.get("index", "")
            orig = str(entry.get("original", "")).replace("\n"," ").replace(","," ")
            cleaned = entry.get("cleaned", entry.get("cleaned_mobile",""))
            reason = entry.get("reason","")
            f.write(f"{idx},{orig},{cleaned},{reason}\n")

    return {
        "new_numbers": len(new_numbers),
        "seeded": seeded_count
    }
