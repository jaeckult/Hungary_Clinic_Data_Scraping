import pandas as pd

# === Configuration ===
CSV_PATH = "UK_Reiki_Prakts_EUROPE.csv"  # <-- Change this to your CSV file path
REQUIRED_FIELDS = {
    "Index": int,
    "Practitioner Name": str,
    "Email": str,
    "Address" : str,
    "Phone": str,
    "Website": str,
    "Google Maps URL": str
}

# === Load CSV ===
try:
    df = pd.read_csv(CSV_PATH)
    print(f"✅ Loaded CSV with {len(df)} rows.")
except FileNotFoundError:
    print(f"❌ File not found: {CSV_PATH}")
    exit(1)
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    exit(1)

# === Field Validation ===
def validate_row(row, row_num):
    errors = []

    for field, expected_type in REQUIRED_FIELDS.items():
        value = row.get(field)

        # Check if field is missing
        if pd.isna(value) or value == '':
            errors.append(f"Row {row_num}: Missing value for '{field}'")
            continue

        # Type checking
        try:
            if expected_type == int:
                int(value)
            elif expected_type == float:
                float(value)
            elif expected_type == str:
                str(value)
        except ValueError:
            errors.append(f"Row {row_num}: Invalid type for '{field}' (expected {expected_type.__name__})")

    return errors

# === Run Validation ===
all_errors = []

for i, row in df.iterrows():
    row_errors = validate_row(row, i + 1)
    all_errors.extend(row_errors)

# === Report ===
if all_errors:
    print("❌ Validation Errors Found:")
    for err in all_errors:
        print(" -", err)
else:
    print("✅ All rows validated successfully.")

