import pandas as pd
from datetime import datetime

# ====================================================
# Load Blocklist (auto-upgrade if old format)
# ====================================================
def load_blocklist(file_path="seen_feedback_mobiles.csv"):
    try:
        df = pd.read_csv(file_path, dtype=str, header=None)
    except Exception:
        return pd.DataFrame(columns=["Mobile", "DateAdded"])

    # Old format: only 1 column (Mobile numbers)
    if df.shape[1] == 1:
        df.columns = ["Mobile"]
        df["DateAdded"] = datetime.today().strftime("%Y-%m-%d")

        # Overwrite file in new format
        df.to_csv(file_path, index=False)

    else:
        df.columns = ["Mobile", "DateAdded"]

    return df

# ====================================================
# Process File (with optional blocklist & cutoff date)
# ====================================================
def process_file(input_path, cleaned_output, flagged_log, apply_blocklist=True, cutoff_date=None):
    df = pd.read_excel(input_path)

    # Simple cleaning: drop duplicates, trim whitespace
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.drop_duplicates()

    new_numbers = 0
    blocklist_file = "seen_feedback_mobiles.csv"

    if apply_blocklist:
        blocklist_df = load_blocklist(blocklist_file)

        # Convert DateAdded to datetime
        blocklist_df["DateAdded"] = pd.to_datetime(blocklist_df["DateAdded"], errors="coerce")

        # Apply cutoff date
        if cutoff_date:
            cutoff_dt = pd.to_datetime(cutoff_date)
            blocklist_df = blocklist_df[blocklist_df["DateAdded"] <= cutoff_dt]

        blocklist = blocklist_df["Mobile"].astype(str).tolist()

        initial_len = len(df)

        # Flagged numbers
        flagged = df[df["Mobile"].astype(str).isin(blocklist)]
        flagged["Mobile"].to_csv(flagged_log, index=False, header=False)

        # Remove blocklisted rows
        df = df[~df["Mobile"].astype(str).isin(blocklist)]
        removed_len = initial_len - len(df)

        # Update blocklist with new flagged numbers (today’s date)
        new_numbers = len(flagged)
        if new_numbers > 0:
            new_entries = pd.DataFrame({
                "Mobile": flagged["Mobile"].astype(str).drop_duplicates(),
                "DateAdded": datetime.today().strftime("%Y-%m-%d")
            })
            new_entries.to_csv(blocklist_file, mode="a", index=False, header=False)
    else:
        # If blocklist is not applied → just empty flagged log
        with open(flagged_log, "w") as f:
            f.write("")

    # Save cleaned file
    df.to_excel(cleaned_output, index=False)

    return {"new_numbers": new_numbers}
