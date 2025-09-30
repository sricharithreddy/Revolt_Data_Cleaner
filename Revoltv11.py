import pandas as pd
import re
from datetime import datetime
import os

# ====================================================
# Utility Functions
# ====================================================
def clean_customer_name(name: str) -> str:
    if pd.isna(name):
        return ""
    name = re.sub(r"[^A-Za-z\s]", "", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()

def clean_mobile_number(num) -> str:
    if pd.isna(num):
        return ""
    num = str(num).strip()
    num = re.sub(r"\D", "", num)  # keep digits only
    if len(num) > 10:
        num = num[-10:]  # take last 10
    if len(num) == 10:
        return num
    return ""

def clean_date(val) -> str:
    if pd.isna(val):
        return ""
    try:
        dt = pd.to_datetime(val, errors="coerce")
        if pd.isna(dt):
            return ""
        day = dt.day
        suffix = "th"
        if day in [1, 21, 31]:
            suffix = "st"
        elif day in [2, 22]:
            suffix = "nd"
        elif day in [3, 23]:
            suffix = "rd"
        return f"{day}{suffix} {dt.strftime('%B')}"
    except Exception:
        return str(val)

# ====================================================
# Load and Save Blocklist
# ====================================================
BLOCKLIST_FILE = "seen_feedback_mobiles.csv"

def load_blocklist():
    if os.path.exists(BLOCKLIST_FILE):
        return pd.read_csv(BLOCKLIST_FILE, dtype=str)
    else:
        return pd.DataFrame(columns=["Mobile Number", "DateAdded"])

def save_blocklist(df: pd.DataFrame):
    df.to_csv(BLOCKLIST_FILE, index=False)

# ====================================================
# Main Processing
# ====================================================
def process_file(input_file: str, cleaned_output: str, flagged_log: str):
    today = datetime.now().strftime("%Y-%m-%d")
    blocklist = load_blocklist()

    writer = pd.ExcelWriter(cleaned_output, engine="xlsxwriter")
    xls = pd.ExcelFile(input_file)

    debug_lines = []

    for sheet in xls.sheet_names:
        df = xls.parse(sheet)

        # Normalize column names aggressively
        normalized_cols = [re.sub(r"[\s\-_]", "", c.strip().lower()) for c in df.columns]
        col_map = dict(zip(df.columns, normalized_cols))
        df.rename(columns=col_map, inplace=True)

        debug_lines.append(f"\nSheet: {sheet}")
        debug_lines.append(f"Columns after normalize: {list(df.columns)}")

        # Standardize names
        rename_rules = {
            "mobilenumber": "Mobile Number",     # covers mobilenum / mobile_number variations
            "buyername": "Customer Name",
            "testridedateandtimeactual": "trscheduleactual",
            "trcompleteddate": "trcompleteddate"
        }
        df.rename(columns=rename_rules, inplace=True)

        # Apply cleaning
        if "Customer Name" in df.columns:
            df["Customer Name"] = df["Customer Name"].apply(clean_customer_name)
        if "Mobile Number" in df.columns:
            df["Mobile Number"] = df["Mobile Number"].apply(clean_mobile_number)

        if "Mobile Number" in df.columns:
            debug_lines.append(f"Sample numbers: {df['Mobile Number'].dropna().unique()[:5]}")

        if "trcompleteddate" in df.columns:
            df["trcompleteddate"] = df["trcompleteddate"].apply(clean_date)
        if "trscheduleactual" in df.columns:
            df["trscheduleactual"] = df["trscheduleactual"].apply(clean_date)

        # ------------------------------------------------
        # Blocklist Handling
        # ------------------------------------------------
        if "Mobile Number" in df.columns:
            sheet_clean = sheet.strip().lower()

            if sheet_clean == "calls":
                # ✅ Add all numbers to blocklist and block immediately
                new_entries = []
                for num in df["Mobile Number"].dropna().unique():
                    if num == "":
                        continue
                    if num not in blocklist["Mobile Number"].values:
                        new_entries.append({"Mobile Number": num, "DateAdded": today})
                if new_entries:
                    debug_lines.append(f"Calls sheet → new entries: {len(new_entries)}")
                    blocklist = pd.concat([blocklist, pd.DataFrame(new_entries)], ignore_index=True)

                before = len(df)
                df = df[~df["Mobile Number"].isin(blocklist["Mobile Number"])]
                debug_lines.append(f"Calls sheet → removed {before - len(df)} rows")

            elif sheet_clean.startswith("tr_completed"):
                # ✅ Add numbers but block only from tomorrow
                new_entries = []
                for num in df["Mobile Number"].dropna().unique():
                    if num == "":
                        continue
                    already_today = not blocklist[
                        (blocklist["Mobile Number"] == num) & (blocklist["DateAdded"] == today)
                    ].empty
                    if not already_today:
                        if num not in blocklist["Mobile Number"].values:
                            new_entries.append({"Mobile Number": num, "DateAdded": today})
                if new_entries:
                    debug_lines.append(f"TR_Completed sheet → new entries: {len(new_entries)}")
                    blocklist = pd.concat([blocklist, pd.DataFrame(new_entries)], ignore_index=True)

                # ✅ Block calls numbers immediately + TR_Completed numbers only if added before today
                calls_numbers = blocklist.loc[
                    (blocklist["DateAdded"] == today), "Mobile Number"
                ].tolist()
                old_numbers = blocklist.loc[
                    (blocklist["DateAdded"] < today), "Mobile Number"
                ].tolist()

                to_block = set(calls_numbers) | set(old_numbers)
                before = len(df)
                df = df[~df["Mobile Number"].isin(to_block)]
                debug_lines.append(f"TR_Completed sheet → removed {before - len(df)} rows")

        # Save cleaned sheet
        df.to_excel(writer, sheet_name=sheet[:31], index=False)

    writer.close()
    save_blocklist(blocklist)

    # Write debug log
    with open(flagged_log, "w", encoding="utf-8") as f:
        f.write("\n".join(debug_lines))

    return {"new_numbers": len(blocklist)}
