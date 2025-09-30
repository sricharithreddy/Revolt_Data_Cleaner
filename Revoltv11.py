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
    # Remove extra spaces, special chars, uppercase consistently
    name = re.sub(r"[^A-Za-z0-9\s]", "", str(name))
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()

def clean_mobile_number(num) -> str:
    if pd.isna(num):
        return ""
    num = re.sub(r"\D", "", str(num))  # Keep only digits
    # Keep 10 digit valid numbers only
    if len(num) == 10:
        return num
    return ""

def clean_date(val) -> str:
    """Convert to '21st September' style format (no year)."""
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

    # Container for cleaned sheets
    writer = pd.ExcelWriter(cleaned_output, engine="xlsxwriter")
    flagged_rows = []

    # Read file
    xls = pd.ExcelFile(input_file)

    for sheet in xls.sheet_names:
        df = xls.parse(sheet)

        # Normalize column names
        df.columns = [c.strip().lower().replace("-", "").replace(" ", "") for c in df.columns]

        # Rename rules
        col_map = {
            "mobilenumber": "Mobile Number",
            "buyername": "Customer Name",
            "testridedateandtimeactual": "trscheduleactual",
            "trcompleteddate": "trcompleteddate"
        }
        df.rename(columns=col_map, inplace=True)

        # Clean columns if present
        if "Customer Name" in df.columns:
            df["Customer Name"] = df["Customer Name"].apply(clean_customer_name)
        if "Mobile Number" in df.columns:
            df["Mobile Number"] = df["Mobile Number"].apply(clean_mobile_number)
        if "trcompleteddate" in df.columns:
            df["trcompleteddate"] = df["trcompleteddate"].apply(clean_date)
        if "trscheduleactual" in df.columns:
            df["trscheduleactual"] = df["trscheduleactual"].apply(clean_date)

        # ------------------------------------------------
        # Blocklist Handling
        # ------------------------------------------------
        if "Mobile Number" in df.columns:
            # For "calls" and "TR_Completed*" sheets → seed blocklist
            if sheet.lower() == "calls" or sheet.lower().startswith("tr_completed"):
                new_entries = []
                for num in df["Mobile Number"].dropna().unique():
                    if num == "":
                        continue
                    # Check if already in blocklist with today's date
                    already_today = not blocklist[
                        (blocklist["Mobile Number"] == num) & (blocklist["DateAdded"] == today)
                    ].empty
                    if not already_today:
                        if num not in blocklist["Mobile Number"].values:
                            new_entries.append({"Mobile Number": num, "DateAdded": today})
                if new_entries:
                    blocklist = pd.concat([blocklist, pd.DataFrame(new_entries)], ignore_index=True)

            # Remove rows with numbers in blocklist (added before today)
            df = df[~df["Mobile Number"].isin(
                blocklist.loc[blocklist["DateAdded"] < today, "Mobile Number"]
            )]

        # Save cleaned sheet
        df.to_excel(writer, sheet_name=sheet[:31], index=False)

    writer.close()
    save_blocklist(blocklist)

    # Return stats
    return {"new_numbers": len(blocklist)}
