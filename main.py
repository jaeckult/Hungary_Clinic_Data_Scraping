#!/usr/bin/env python3
"""
Google Maps Scraping - Main Application Entry Point

A comprehensive tool for scraping and processing Google Maps business data.
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import settings
from src.utils.logger import setup_logging, get_logger
from src.data_processing.data_import_tool import DataImportTool


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description="Google Maps Scraping Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py import --csv data/raw/businesses.csv
  python main.py import --gsheet "https://docs.google.com/spreadsheets/d/..."
  python main.py scrape --query "reiki practitioners" --location "New York"
  python main.py process --input data/raw/ --output data/processed/
  python main.py validate --file data/processed/businesses.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import data from various sources')
    import_parser.add_argument('--csv', type=str, help='Path to CSV file')
    import_parser.add_argument('--gsheet', type=str, help='Google Sheets URL')
    import_parser.add_argument('--config', type=str, help='Configuration file path')
    import_parser.add_argument('--output', type=str, help='Output file path')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape data from Google Maps')
    scrape_parser.add_argument('--query', type=str, required=True, help='Search query')
    scrape_parser.add_argument('--location', type=str, required=True, help='Location to search')
    scrape_parser.add_argument('--limit', type=int, default=100, help='Maximum results to scrape')
    scrape_parser.add_argument('--output', type=str, help='Output file path')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process and clean data')
    process_parser.add_argument('--input', type=str, required=True, help='Input directory or file')
    process_parser.add_argument('--output', type=str, required=True, help='Output directory')
    process_parser.add_argument('--format', type=str, default='csv', help='Output format')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate data quality')
    validate_parser.add_argument('--file', type=str, required=True, help='File to validate')
    validate_parser.add_argument('--rules', type=str, help='Validation rules file')
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--config-file', type=str, help='Custom configuration file')
    
    return parser


def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else settings.logging.level
    logger = setup_logging(
        name="google_maps_scraping",
        log_level=log_level,
        log_file=settings.logging.file,
        console_output=settings.logging.console_output
    )
    
    logger.info("Starting Google Maps Scraping application", version=settings.app.version)
    
    try:
        if args.command == 'import':
            handle_import(args, logger)
        elif args.command == 'scrape':
            handle_scrape(args, logger)
        elif args.command == 'process':
            handle_process(args, logger)
        elif args.command == 'validate':
            handle_validate(args, logger)
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


def handle_import(args, logger):
    """Handle the import command."""
    logger.info("Processing import command")
    
    import_tool = DataImportTool(args.config)
    
    if args.csv:
        source_type = "csv"
        source_path = args.csv
    elif args.gsheet:
        source_type = "gsheet"
        source_path = args.gsheet
    else:
        logger.error("Please specify either --csv or --gsheet")
        sys.exit(1)
    
    try:
        df = import_tool.import_data(source=source_path, source_type=source_type)
        
        if args.output:
            df.to_csv(args.output, index=False)
            logger.info(f"Data saved to: {args.output}")
        
        logger.info(f"Successfully imported {len(df)} records")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


def handle_scrape(args, logger):
    """Handle the scrape command."""
    logger.info("Processing scrape command", query=args.query, location=args.location)
    
    # TODO: Implement scraping functionality
    logger.warning("Scraping functionality not yet implemented")
    
    # Placeholder for future implementation
    logger.info(f"Would scrape {args.limit} results for '{args.query}' in '{args.location}'")


def handle_process(args, logger):
    """Handle the process command."""
    logger.info("Processing data", input=args.input, output=args.output)
    
    # TODO: Implement data processing functionality
    logger.warning("Data processing functionality not yet implemented")
    
    # Placeholder for future implementation
    logger.info(f"Would process data from {args.input} to {args.output} in {args.format} format")


def handle_validate(args, logger):
    """Handle the validate command."""
    logger.info("Processing validation", file=args.file)
    
    # TODO: Implement validation functionality
    logger.warning("Validation functionality not yet implemented")
    
    # Placeholder for future implementation
    logger.info(f"Would validate data in {args.file}")


if __name__ == "__main__":
    main()
