import pandas as pd
import argparse
import sys

def import_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        print(f"✅ Successfully loaded CSV from: {file_path}")
        return df
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        sys.exit(1)

def import_google_sheet(sheet_url):
    try:
        # Convert Google Sheets link to export format
        if "edit" in sheet_url:
            csv_url = sheet_url.replace("/edit", "/export?format=csv")
        elif "gid=" in sheet_url:
            csv_url = sheet_url.split("/")[0] + "/export?format=csv"
        else:
            raise ValueError("Unsupported Google Sheets link format")
        
        df = pd.read_csv(csv_url)
        print(f"✅ Successfully loaded Google Sheet from: {sheet_url}")
        return df
    except Exception as e:
        print(f"❌ Error loading Google Sheet: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="📥 Import data from CSV or Google Sheets")
    parser.add_argument('--csv', type=str, help="Path to local CSV file")
    parser.add_argument('--gsheet', type=str, help="Public Google Sheets URL")
    args = parser.parse_args()

    if args.csv:
        df = import_csv(args.csv)
    elif args.gsheet:
        df = import_google_sheet(args.gsheet)
    else:
        print("❗ Please specify either --csv or --gsheet")
        sys.exit(1)

    print("\n📊 First 5 rows of imported data:")
    print(df.head())

if __name__ == "__main__":
    main()
