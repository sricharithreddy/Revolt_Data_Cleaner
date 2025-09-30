import os
import re
from datetime import datetime
import pandas as pd

# ====================================================
# Utility Functions
# ====================================================

def clean_customer_name(name: str) -> str:
    """Keep only letters & spaces, squeeze spaces, Title Case."""
    if pd.isna(name):
        return ""
    name = re.sub(r"[^A-Za-z\s]", "", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()

def clean_mobile_number(num) -> str:
    """Normalize to last 10 digits; return '' if not 10 digits."""
    if pd.isna(num):
        return ""
    s = str(num).strip()
    digits = re.sub(r"\D", "", s)
    if len(digits) > 10:
        digits = digits[-10:]
    if len(digits) == 10:
        return digits
    return ""

def clean_date(val) -> str:
    """Format to '21st September' (no year)."""
    if pd.isna(val):
        return ""
    try:
        dt = pd.to_datetime(val, errors="coerce")
        if pd.isna(dt):
            return ""
        day = dt.day
        if day in (1, 21, 31):
            suf = "st"
        elif day in (2, 22):
            suf = "nd"
        elif day in (3, 23):
            suf = "rd"
        else:
            suf = "th"
        return f"{day}{suf} {dt.strftime('%B')}"
    except Exception:
        return str(val)

# ====================================================
# Blocklist IO
# ====================================================

BLOCKLIST_FILE = "seen_feedback_mobiles.csv"

def load_blocklist() -> pd.DataFrame:
    """Load blocklist with columns ['Mobile Number','DateAdded']."""
    if os.path.exists(BLOCKLIST_FILE):
        return pd.read_csv(BLOCKLIST_FILE, dtype=str)
    return pd.DataFrame(columns=["Mobile Number", "DateAdded"])

def save_blocklist(df: pd.DataFrame) -> None:
    df.to_csv(BLOCKLIST_FILE, index=False)

# ====================================================
# Main Processing
# ====================================================

def process_file(input_file: str, cleaned_output: str, flagged_log: str):
    """
    - Any sheet: add numbers with DateAdded=today if not in blocklist
    - Block only if DateAdded < today
    """
    today = datetime.now().strftime("%Y-%m-%d")
    blocklist = load_blocklist()
    new_added_count = 0

    writer = pd.ExcelWriter(cleaned_output, engine="xlsxwriter")
    xls = pd.ExcelFile(input_file)

    debug_lines = []

    for sheet in xls.sheet_names:
        df = xls.parse(sheet)

        # Normalize column names
        normalized = [re.sub(r"[\s\-_]", "", str(c).strip().lower()) for c in df.columns]
        df.rename(columns=dict(zip(df.columns, normalized)), inplace=True)

        debug_lines.append(f"\nSheet: {sheet}")
        debug_lines.append(f"Columns after normalize: {list(df.columns)}")

        # Standardize headers
        rename_rules = {
            "mobilenumber": "Mobile Number",
            "buyername": "Customer Name",
            "testridedateandtimeactual": "trscheduleactual",
            "trcompleteddate": "trcompleteddate"
        }
        df.rename(columns=rename_rules, inplace=True)

        # Clean columns
        if "Customer Name" in df.columns:
            df["Customer Name"] = df["Customer Name"].apply(clean_customer_name)
        if "Mobile Number" in df.columns:
            df["Mobile Number"] = df["Mobile Number"].apply(clean_mobile_number)
        if "trcompleteddate" in df.columns:
            df["trcompleteddate"] = df["trcompleteddate"].apply(clean_date)
        if "trscheduleactual" in df.columns:
            df["trscheduleactual"] = df["trscheduleactual"].apply(clean_date)

        # Blocklist handling
        if "Mobile Number" in df.columns:
            nums = [n for n in df["Mobile Number"].dropna().unique() if n]
            existing_set = set(blocklist["Mobile Number"].astype(str))
            truly_new = [n for n in nums if n not in existing_set]

            if truly_new:
                blocklist = pd.concat(
                    [blocklist, pd.DataFrame({"Mobile Number": truly_new, "DateAdded": today})],
                    ignore_index=True
                )
                new_added_count += len(truly_new)
                debug_lines.append(f"Sheet {sheet} → new added: {len(truly_new)}")

            before = len(df)
            df = df[~df["Mobile Number"].isin(
                blocklist.loc[blocklist["DateAdded"] < today, "Mobile Number"]
            )]
            debug_lines.append(f"Sheet {sheet} → removed {before - len(df)} rows")

        df.to_excel(writer, sheet_name=sheet[:31], index=False)

    writer.close()
    save_blocklist(blocklist)

    with open(flagged_log, "w", encoding="utf-8") as f:
        f.write("\n".join(debug_lines))

    return {"new_numbers": new_added_count}
