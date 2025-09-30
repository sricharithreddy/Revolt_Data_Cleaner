import pandas as pd
import re
import os
import json
import argparse
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
        logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                     "cleaned": name, "reason": "empty_or_invalid_input"})
        return False
    lower_name = name.lower().strip()
    blacklist = [
        "joker","k","ccc","aaa","busy","king","spam","failureboys",
        "radhe radhe","jai mata di","jaisairam","shubh din",
        "emergency enquiry","spam callers","black world",
        "indian soldiers lover","miss youu guruji","sss","adc",
        "dsp","ettlement","ww wmeresathi","bsnl fiber","null",
        "lets learn","typing","always be positive","it doesnt matter",
        "next","rss","vvv","ggg","kk","ok",
        "lead","test","dummy","na","abc","hotel"
    ]
    for word in blacklist:
        if lower_name == word:
            logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                         "cleaned": name, "reason": f"blacklist_match:{word}"})
            return False
    if len(lower_name) < 2:
        logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                     "cleaned": name, "reason": "too_short"})
        return False
    if re.match(r'^\d+$', lower_name):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                     "cleaned": name, "reason": "numeric"})
        return False
    if not re.search(r'[aeiou]', lower_name):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                     "cleaned": name, "reason": "no_vowels"})
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
            logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                         "cleaned": "", "reason": "empty_or_invalid_input"})
            return ""
    except Exception:
        if not name:
            logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                         "cleaned": "", "reason": "empty_or_invalid_input"})
            return ""
    name = name.strip()
    bike_models_to_remove = ["RV1","RV400","RV400BRZ","RV1+","RV BLAZEX","RV-400","RV 400","RV BLAZE","RV BLAZE X"]
    pattern = re.compile("(" + "|".join(re.escape(w) for w in bike_models_to_remove) + ")", re.IGNORECASE)
    name = pattern.sub("", name).strip()
    name = re.sub(r"[-\u2013\u2014]", "", name)
    name = re.sub(r"[_\.0-9!@#$%^&*()+=?/,<>;:\"\\|{}\[\]~`]", "", name)
    name = name.replace('\u00A0',' ')
    name = re.sub(r'[\u2000-\u200B\u202F\u205F\uFEFF]',' ', name)
    name = name.replace('\u200D','')
    name = re.sub(r'\s+',' ', name).strip()
    if re.match(r'^(?:[A-Za-z]\s+){2,}[A-Za-z]$', name.strip()):
        return re.sub(r'\s+','', name).capitalize()
    tokens = re.split(r'\s+', name.strip())
    cleaned_tokens = [re.sub(r'[^A-Za-z]','',t) for t in tokens]
    single_letter_count = sum(1 for t in cleaned_tokens if len(t)==1)
    if len(cleaned_tokens)>=3 and single_letter_count>=max(2,int(len(cleaned_tokens)*0.5)):
        letters_only = ''.join([t for t in cleaned_tokens if len(t)==1])
        if len(letters_only)>=3:
            return letters_only.capitalize()
    letters_only = re.sub(r'[^A-Za-z]','', name)
    space_count = len(re.findall(r'\s', name))
    if letters_only and len(letters_only)>=3 and space_count>=max(1,len(letters_only)-1):
        return letters_only.capitalize()
    name = re.sub(r'\s+',' ', name).strip()
    if re.match(r'^\d+$', name.strip()):
        logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                     "cleaned": "", "reason": "purely_numeric_after_removal"})
        return ""
    cleaned = re.sub(r"[^a-zA-Z\s']", "", name).strip()
    if not cleaned:
        logs.append({"index": row_index if row_index is not None else "", "original": original_name,
                     "cleaned": "", "reason": "no_valid_characters_after_cleaning"})
        return ""
    cleaned = split_camel_case(cleaned)
    cleaned = ' '.join(w.capitalize() for w in cleaned.split())
    try:
        orig = str(original_name) if original_name is not None else ""
        has_lower_upper = bool(re.search(r'[a-z][A-Z]', orig))
        had_space = bool(re.search(r'\s', orig))
        tokens_after = cleaned.split()
        if has_lower_upper and not had_space and len(tokens_after)>=2 and len(tokens_after[-1])==1:
            cleaned = ''.join(tokens_after).capitalize()
    except Exception:
        pass
    if not is_sensible_name(cleaned, original_name, row_index, logs):
        return ""
    return cleaned

def clean_mobile_number(raw_mobile: str, row_index: Optional[int], logs: List[Dict]) -> str:
    if pd.isna(raw_mobile):
        logs.append({"index": row_index if row_index is not None else "", "original": raw_mobile,
                     "cleaned_mobile": "", "reason": "mobile_is_na"})
        return ""
    digits = re.sub(r'\D','', str(raw_mobile).strip())
    if len(digits)==10:
        return digits
    if len(digits)>10:
        return digits[-10:]
    logs.append({"index": row_index if row_index is not None else "", "original": raw_mobile,
                 "cleaned_mobile": "", "reason": f"too_short_digits:{digits}"})
    return ""

def process_file(input_file_path: str, output_file_path: str, flagged_log_path: str = "flagged_names.txt"):
    logs: List[Dict] = []
    rename_rules = {
        "mobilenumber": "Mobile Number",
        "buyername": "Customer Name",
        "testridedateandtimeactual": "trscheduleactual"
    }

    if input_file_path.lower().endswith(('.xlsx','.xls')):
        all_sheets = pd.read_excel(input_file_path, sheet_name=None)
    elif input_file_path.lower().endswith('.csv'):
        all_sheets = {"Sheet1": pd.read_csv(input_file_path)}
    else:
        raise ValueError("Unsupported format")

    # Load blocklist
    blocklist_file = "seen_feedback_mobiles.csv"
    seen_set = set()
    if os.path.exists(blocklist_file):
        seen_df = pd.read_csv(blocklist_file)
        seen_set = set(str(x).strip() for x in seen_df['Mobile Number'] if str(x).strip())

    new_numbers = set()
    cleaned_sheets = {}
    for sheet_name, df in all_sheets.items():
        if 'opportunityid' in df.columns:
            df.rename(columns={'opportunityid':'opportunity_id'}, inplace=True)
        if 'Mobile Number' in df.columns:
            df['Mobile Number'] = [clean_mobile_number(val, idx, logs) for idx, val in df['Mobile Number'].items()]
            df = df[~df['Mobile Number'].isin(seen_set)]
        if 'Customer Name' in df.columns:
            df['Customer Name'] = [clean_customer_name(val, idx, logs) for idx, val in df['Customer Name'].items()]
        if sheet_name.lower() == "tr_completed" and 'Mobile Number' in df.columns:
            new_numbers.update([str(x).strip() for x in df['Mobile Number'] if str(x).strip()])
        cleaned_sheets[sheet_name] = df

    if new_numbers:
        updated_numbers = sorted(seen_set.union(new_numbers))
        pd.Series(updated_numbers, name="Mobile Number").to_csv(blocklist_file, index=False)

    with pd.ExcelWriter(output_file_path, engine="xlsxwriter") as writer:
        for sheet_name, df in cleaned_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    with open(flagged_log_path,"w",encoding="utf-8") as f:
        f.write("index,original,cleaned,reason\n")
        for entry in logs:
            idx=entry.get("index","")
            orig=str(entry.get("original","")).replace('\n',' ').replace(',',' ')
            reason=entry.get("reason","")
            cleaned=entry.get("cleaned",entry.get("cleaned_mobile",""))
            f.write(f"{idx},{orig},{cleaned},{reason}\n")

    return len(new_numbers)  # return how many new numbers were added
