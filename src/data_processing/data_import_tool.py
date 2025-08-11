#!/usr/bin/env python3
"""
Data Import Tool

A comprehensive tool for importing data from various sources including CSV files
and Google Sheets. Provides robust error handling, logging, and data validation.

Author: Data Import Tool
Version: 1.0.0
"""

import pandas as pd
import argparse
import sys
import logging
import os
from typing import Optional, Union, Dict, Any
from urllib.parse import urlparse
from pathlib import Path
import json


class DataImporterConfig:
    """Configuration class for data import settings."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self._setup_logging()
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "data_import.log"
            },
            "data": {
                "encoding": "utf-8",
                "chunk_size": 10000,
                "max_rows": None
            },
            "google_sheets": {
                "timeout": 30,
                "retry_attempts": 3
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logging.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logging.warning(f"Failed to load config file: {e}. Using defaults.")
        
        return default_config
    
    def _setup_logging(self):
        """Configure logging based on settings."""
        log_config = self.config["logging"]
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format=log_config["format"],
            handlers=[
                logging.FileHandler(log_config["file"]),
                logging.StreamHandler(sys.stdout)
            ]
        )


class DataValidator:
    """Class for validating imported data."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: Optional[list] = None) -> Dict[str, Any]:
        """Validate the imported dataframe."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        # Basic dataframe validation
        if df.empty:
            validation_results["is_valid"] = False
            validation_results["errors"].append("DataFrame is empty")
            return validation_results
        
        # Check for required columns
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                validation_results["is_valid"] = False
                validation_results["errors"].append(f"Missing required columns: {missing_columns}")
        
        # Generate statistics
        validation_results["stats"] = {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "null_counts": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum()
        }
        
        # Check for warnings
        if validation_results["stats"]["duplicate_rows"] > 0:
            validation_results["warnings"].append(f"Found {validation_results['stats']['duplicate_rows']} duplicate rows")
        
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if null_percentage > 10:
            validation_results["warnings"].append(f"High percentage of null values: {null_percentage:.2f}%")
        
        return validation_results


class CSVImporter:
    """Class for handling CSV file imports."""
    
    def __init__(self, config: DataImporterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def import_csv(self, file_path: str) -> pd.DataFrame:
        """Import data from a CSV file with comprehensive error handling."""
        self.logger.info(f"Attempting to import CSV from: {file_path}")
        
        # Validate file path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        if not file_path.lower().endswith('.csv'):
            raise ValueError(f"File does not appear to be a CSV: {file_path}")
        
        try:
            # Read CSV with configuration
            data_config = self.config.config["data"]
            df = pd.read_csv(
                file_path,
                encoding=data_config["encoding"],
                nrows=data_config["max_rows"],
                chunksize=data_config["chunk_size"]
            )
            
            # Handle chunked reading
            if isinstance(df, pd.io.parsers.TextFileReader):
                df = pd.concat(df, ignore_index=True)
            
            self.logger.info(f"✅ Successfully loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSV parsing error: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error loading CSV: {e}")
            raise


class GoogleSheetsImporter:
    """Class for handling Google Sheets imports."""
    
    def __init__(self, config: DataImporterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def import_google_sheet(self, sheet_url: str) -> pd.DataFrame:
        """Import data from a Google Sheet with comprehensive error handling."""
        self.logger.info(f"Attempting to import Google Sheet from: {sheet_url}")
        
        # Validate URL
        if not self._is_valid_google_sheets_url(sheet_url):
            raise ValueError("Invalid Google Sheets URL format")
        
        try:
            # Convert Google Sheets link to export format
            csv_url = self._convert_to_csv_url(sheet_url)
            
            # Read CSV with configuration
            data_config = self.config.config["data"]
            gs_config = self.config.config["google_sheets"]
            
            df = pd.read_csv(
                csv_url,
                encoding=data_config["encoding"],
                nrows=data_config["max_rows"],
                timeout=gs_config["timeout"]
            )
            
            self.logger.info(f"✅ Successfully loaded Google Sheet: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error loading Google Sheet: {e}")
            raise
    
    def _is_valid_google_sheets_url(self, url: str) -> bool:
        """Validate if the URL is a proper Google Sheets URL."""
        try:
            parsed = urlparse(url)
            return "docs.google.com" in parsed.netloc and "spreadsheets" in url
        except:
            return False
    
    def _convert_to_csv_url(self, sheet_url: str) -> str:
        """Convert Google Sheets URL to CSV export format."""
        if "/edit" in sheet_url:
            return sheet_url.replace("/edit", "/export?format=csv")
        elif "gid=" in sheet_url:
            # Handle URLs with specific sheet IDs
            base_url = sheet_url.split("/")[0]
            return f"{base_url}/export?format=csv"
        else:
            # Assume it's already in the correct format or add export parameter
            if "export" not in sheet_url:
                return f"{sheet_url}/export?format=csv"
            return sheet_url


class DataImportTool:
    """Main class for the data import tool."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = DataImporterConfig(config_file)
        self.logger = logging.getLogger(__name__)
        self.csv_importer = CSVImporter(self.config)
        self.gsheets_importer = GoogleSheetsImporter(self.config)
        self.validator = DataValidator()
    
    def import_data(self, source: str, source_type: str, required_columns: Optional[list] = None) -> pd.DataFrame:
        """Main method to import data from various sources."""
        self.logger.info(f"Starting data import from {source_type}: {source}")
        
        try:
            if source_type == "csv":
                df = self.csv_importer.import_csv(source)
            elif source_type == "gsheet":
                df = self.gsheets_importer.import_google_sheet(source)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            # Validate the imported data
            validation_results = self.validator.validate_dataframe(df, required_columns)
            
            # Log validation results
            self._log_validation_results(validation_results)
            
            if not validation_results["is_valid"]:
                raise ValueError(f"Data validation failed: {validation_results['errors']}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Data import failed: {e}")
            raise
    
    def _log_validation_results(self, results: Dict[str, Any]):
        """Log validation results."""
        if results["errors"]:
            for error in results["errors"]:
                self.logger.error(f"Validation error: {error}")
        
        if results["warnings"]:
            for warning in results["warnings"]:
                self.logger.warning(f"Validation warning: {warning}")
        
        self.logger.info(f"Data statistics: {results['stats']}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="📥 Advanced Data Import Tool - Import data from CSV or Google Sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python data_import_tool.py --csv data.csv
  python data_import_tool.py --gsheet "https://docs.google.com/spreadsheets/d/..."
  python data_import_tool.py --csv data.csv --config config.json
  python data_import_tool.py --csv data.csv --validate --output processed_data.csv
        """
    )
    
    parser.add_argument(
        '--csv', 
        type=str, 
        help="Path to local CSV file"
    )
    parser.add_argument(
        '--gsheet', 
        type=str, 
        help="Public Google Sheets URL"
    )
    parser.add_argument(
        '--config', 
        type=str, 
        help="Path to configuration JSON file"
    )
    parser.add_argument(
        '--validate', 
        action='store_true',
        help="Perform data validation after import"
    )
    parser.add_argument(
        '--output', 
        type=str, 
        help="Output file path for processed data"
    )
    parser.add_argument(
        '--required-columns', 
        type=str, 
        nargs='+',
        help="List of required columns for validation"
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help="Enable verbose logging"
    )
    
    return parser


def main():
    """Main entry point for the data import tool."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if not args.csv and not args.gsheet:
        parser.error("Please specify either --csv or --gsheet")
    
    if args.csv and args.gsheet:
        parser.error("Please specify only one source (--csv OR --gsheet)")
    
    try:
        # Initialize the import tool
        import_tool = DataImportTool(args.config)
        
        # Set source type and path
        source_type = "csv" if args.csv else "gsheet"
        source_path = args.csv or args.gsheet
        
        # Import data
        df = import_tool.import_data(
            source=source_path,
            source_type=source_type,
            required_columns=args.required_columns
        )
        
        # Display results
        print(f"\n📊 Successfully imported data:")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        print(f"\n📋 First 5 rows of imported data:")
        print(df.head().to_string())
        
        print(f"\n📈 Column information:")
        print(df.info())
        
        # Save output if specified
        if args.output:
            df.to_csv(args.output, index=False)
            print(f"\n💾 Data saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
