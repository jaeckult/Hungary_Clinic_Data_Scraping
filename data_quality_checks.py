import pandas as pd

# === Configuration ===
INPUT_CSV = "USA_Reiki_Prakts.csv"  # Original file
OUTPUT_CSV = "USA_data_cleaned.csv"  # Cleaned output
IDENTIFY_DUPLICATES_ON = ["Index", "Email", "Phone", "Practitioner Name", "Website", "Google Maps URL"]  # Columns to identify duplicates
REQUIRED_FIELDS = ["Index", "Email", "Phone", "Practitioner Name", "Website", "Google Maps URL"]

# === Load CSV ===
try:
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded '{INPUT_CSV}' with {len(df)} rows.")
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    exit(1)

# === 1. Trim Whitespace for All String Columns ===
str_cols = df.select_dtypes(include="object").columns
df[str_cols] = df[str_cols].apply(lambda col: col.str.strip() if col.dtype == "object" else col)

# === 2. Check for Missing Values ===
missing_rows = df[REQUIRED_FIELDS].isnull().any(axis=1)
if missing_rows.any():
    print(f"⚠️ Found {missing_rows.sum()} rows with missing values in required fields.")
    df = df[~missing_rows]
else:
    print("✅ No missing values in required fields.")

# === 3. Remove Duplicates ===
before = len(df)
df = df.drop_duplicates(subset=IDENTIFY_DUPLICATES_ON, keep="first")
removed = before - len(df)
if removed > 0:
    print(f"⚠️ Removed {removed} duplicate rows.")
else:
    print("✅ No duplicates found.")

# === 4. Save Cleaned Data ===
df.to_csv(OUTPUT_CSV, index=False)
print(f"\n✅ Cleaned data saved to '{OUTPUT_CSV}' ({len(df)} rows).")
