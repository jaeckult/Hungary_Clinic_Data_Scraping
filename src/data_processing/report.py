import pandas as pd

# === Configuration ===
INPUT_CSV = "UK_Reiki_Prakts_EUROPE.csv"
OUTPUT_CLEANED_CSV = "data_cleaned.csv"
OUTPUT_PROBLEMATIC_CSV = "europe_problematic_records.csv"
IDENTIFY_DUPLICATES_ON = ["Index", "Email", "Phone", "Practitioner Name", "Website", "Google Maps URL"]  # Columns to identify duplicates
REQUIRED_FIELDS = ["Index", "Email", "Phone", "Practitioner Name", "Website", "Google Maps URL"]

# === Load CSV ===
try:
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded '{INPUT_CSV}' with {len(df)} rows.")
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    exit(1)

# === Clean Whitespace ===
str_cols = df.select_dtypes(include="object").columns
df[str_cols] = df[str_cols].apply(lambda col: col.str.strip() if col.dtype == "object" else col)

# === Identify Missing Rows ===
missing_mask = df[REQUIRED_FIELDS].isnull().any(axis=1)
missing_rows = df[missing_mask].copy()
print(f"⚠️ {len(missing_rows)} rows with missing required fields.")

# === Identify Duplicates ===
duplicate_mask = df.duplicated(subset=IDENTIFY_DUPLICATES_ON, keep='first')
duplicate_rows = df[duplicate_mask].copy()
print(f"⚠️ {len(duplicate_rows)} duplicate rows found.")

# === Combine and Save Problematic Rows ===
problematic_rows = pd.concat([missing_rows, duplicate_rows]).drop_duplicates()
if not problematic_rows.empty:
    problematic_rows.to_csv(OUTPUT_PROBLEMATIC_CSV, index=False)
    print(f"📝 Problematic rows saved to '{OUTPUT_PROBLEMATIC_CSV}'")
else:
    print("✅ No problematic rows to report.")

# === Clean Data ===
df_cleaned = df.drop(index=problematic_rows.index)
df_cleaned.to_csv(OUTPUT_CLEANED_CSV, index=False)
print(f"\n✅ Cleaned data saved to '{OUTPUT_CLEANED_CSV}' ({len(df_cleaned)} rows).")
