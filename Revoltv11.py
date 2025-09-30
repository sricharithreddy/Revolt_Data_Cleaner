# ====================================================
# Main Processing (Updated)
# ====================================================
def process_file(input_file: str, cleaned_output: str, flagged_log: str):
    today = datetime.now().strftime("%Y-%m-%d")
    blocklist = load_blocklist()

    writer = pd.ExcelWriter(cleaned_output, engine="xlsxwriter")
    xls = pd.ExcelFile(input_file)

    debug_lines = []

    for sheet in xls.sheet_names:
        df = xls.parse(sheet)

        # Normalize column names aggressively (No changes here)
        normalized_cols = [re.sub(r"[\s\-_]", "", c.strip().lower()) for c in df.columns]
        col_map = dict(zip(df.columns, normalized_cols))
        df.rename(columns=col_map, inplace=True)

        debug_lines.append(f"\nSheet: {sheet}")
        debug_lines.append(f"Columns after normalize: {list(df.columns)}")

        # Standardize names (No changes here)
        rename_rules = {
            "mobilenumber": "Mobile Number",
            "buyername": "Customer Name",
            "testridedateandtimeactual": "trscheduleactual",
            "trcompleteddate": "trcompleteddate"
        }
        df.rename(columns=rename_rules, inplace=True)

        # Apply cleaning (No changes here)
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
        # Blocklist Handling (MODIFIED SECTION)
        # ------------------------------------------------
        if "Mobile Number" in df.columns:
            sheet_clean = sheet.strip().lower()

            if sheet_clean == "calls":
                # ✅ The logic to add numbers from the 'calls' sheet has been removed.
                # We will now ONLY filter this sheet against the existing blocklist.
                debug_lines.append(f"Calls sheet → applying existing blocklist...")
                
                before = len(df)
                # This line is unchanged, but its behavior is different now.
                # It filters using the blocklist loaded at the start, without adding new numbers from this sheet.
                df = df[~df["Mobile Number"].isin(blocklist["Mobile Number"])]
                debug_lines.append(f"Calls sheet → removed {before - len(df)} rows")

            elif sheet_clean.startswith("tr_completed"):
                # ✅ This logic remains the same. It adds numbers from this sheet to be blocked tomorrow.
                new_entries = []
                for num in df["Mobile Number"].dropna().unique():
                    if num == "":
                        continue
                    # Check if the number is already in the blocklist
                    if num not in blocklist["Mobile Number"].values:
                        new_entries.append({"Mobile Number": num, "DateAdded": today})
                
                if new_entries:
                    debug_lines.append(f"TR_Completed sheet → new entries to blocklist: {len(new_entries)}")
                    blocklist = pd.concat([blocklist, pd.DataFrame(new_entries)], ignore_index=True)

                # ✅ The filtering logic for this sheet is simplified for clarity.
                # We block any number that was added to the blocklist BEFORE today.
                # This ensures numbers added today from this very sheet are NOT blocked.
                numbers_to_block = blocklist.loc[
                    blocklist["DateAdded"] < today, "Mobile Number"
                ].unique()

                before = len(df)
                df = df[~df["Mobile Number"].isin(numbers_to_block)]
                debug_lines.append(f"TR_Completed sheet → removed {before - len(df)} rows based on previous days' entries")

        # Save cleaned sheet
        df.to_excel(writer, sheet_name=sheet[:31], index=False)

    writer.close()
    save_blocklist(blocklist)

    # Write debug log
    with open(flagged_log, "w", encoding="utf-8") as f:
        f.write("\n".join(debug_lines))

    return {"new_numbers": len(blocklist)}
