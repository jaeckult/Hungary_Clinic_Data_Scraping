# Google Maps Scraping Project

A comprehensive and scalable tool for scraping and processing Google Maps business data with advanced data validation, processing, and export capabilities.

## 🏗️ Project Structure

```
google-maps-scraping/
├── src/                          # Source code
│   ├── core/                     # Core functionality
│   ├── scrapers/                 # Web scraping modules
│   │   ├── index.js              # Node.js scraper
│   │   ├── package.json          # Node.js dependencies
│   │   └── node_modules/         # Node.js modules
│   ├── data_processing/          # Data processing modules
│   │   ├── data_import_tool.py   # Data import functionality
│   │   ├── data_quality_checks.py # Data quality validation
│   │   ├── data_validator.py     # Data validation
│   │   └── report.py             # Reporting functionality
│   ├── utils/                    # Utility functions
│   │   └── logger.py             # Advanced logging
│   └── config/                   # Configuration management
│       └── settings.py           # Settings loader
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── data/                         # Data storage
│   ├── raw/                      # Raw data files
│   ├── processed/                # Processed data
│   └── exports/                  # Export files
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   └── user_guide/               # User guides
├── scripts/                      # Utility scripts
├── deployment/                   # Deployment files
│   └── Dockerfile                # Docker configuration
├── config/                       # Configuration files
│   └── settings.yaml             # Main configuration
├── logs/                         # Log files
├── main.py                       # Main application entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Features

### Core Functionality
- **Multi-source Data Import**: CSV files, Google Sheets, and more
- **Advanced Data Validation**: Comprehensive data quality checks
- **Structured Logging**: JSON-formatted logs with performance tracking
- **Configuration Management**: YAML-based configuration with environment overrides
- **Modular Architecture**: Scalable and maintainable code structure

### Data Processing
- **Data Cleaning**: Automated data cleaning and standardization
- **Quality Checks**: Validation of data integrity and completeness
- **Export Options**: Multiple output formats (CSV, JSON, Excel)
- **Chunked Processing**: Memory-efficient handling of large datasets

### Web Scraping (Planned)
- **Google Maps Integration**: Automated business data extraction
- **Rate Limiting**: Respectful scraping with configurable delays
- **Proxy Support**: Rotating proxy support for large-scale scraping
- **Error Handling**: Robust error recovery and retry mechanisms

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+ (for JavaScript scrapers)
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd google-maps-scraping
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   cd src/scrapers
   npm install
   cd ../..
   ```

4. **Configure the application**
   ```bash
   cp config/settings.yaml config/settings.local.yaml
   # Edit config/settings.local.yaml with your settings
   ```

## 🛠️ Usage

### Command Line Interface

The application provides a comprehensive CLI with multiple commands:

#### Import Data
```bash
# Import from CSV file
python main.py import --csv data/raw/businesses.csv

# Import from Google Sheets
python main.py import --gsheet "https://docs.google.com/spreadsheets/d/..."

# Import with custom configuration
python main.py import --csv data/raw/businesses.csv --config config/settings.local.yaml
```

#### Scrape Data (Planned)
```bash
# Scrape Google Maps data
python main.py scrape --query "reiki practitioners" --location "New York" --limit 100

# Scrape with custom output
python main.py scrape --query "yoga studios" --location "Los Angeles" --output data/raw/yoga_studios.csv
```

#### Process Data (Planned)
```bash
# Process and clean data
python main.py process --input data/raw/ --output data/processed/

# Process with specific format
python main.py process --input data/raw/businesses.csv --output data/processed/ --format json
```

#### Validate Data (Planned)
```bash
# Validate data quality
python main.py validate --file data/processed/businesses.csv

# Validate with custom rules
python main.py validate --file data/processed/businesses.csv --rules config/validation_rules.yaml
```

### Python API

You can also use the application programmatically:

```python
from src.data_processing.data_import_tool import DataImportTool
from src.config.settings import settings

# Initialize the import tool
import_tool = DataImportTool()

# Import data
df = import_tool.import_data(
    source="data/raw/businesses.csv",
    source_type="csv",
    required_columns=["name", "address", "phone"]
)

# Process the data
print(f"Imported {len(df)} records")
print(df.head())
```

## ⚙️ Configuration

The application uses YAML-based configuration with environment variable overrides:

### Main Configuration (`config/settings.yaml`)

```yaml
# Application settings
app:
  name: "Google Maps Scraping"
  version: "1.0.0"
  environment: "development"
  debug: true

# Logging configuration
logging:
  level: "INFO"
  file: "logs/app.log"
  console_output: true

# Data processing settings
data:
  encoding: "utf-8"
  chunk_size: 10000
  backup_original: true

# Scraping settings
scraping:
  google_maps:
    search_delay: 2.0
    max_retries: 3
    timeout: 30
```

### Environment Variables

You can override configuration with environment variables:

```bash
export GOOGLE_MAPS_API_KEY="your-api-key"
export LOG_LEVEL="DEBUG"
export ENVIRONMENT="production"
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Test Structure
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Performance Tests**: Test scalability and performance

## 📊 Data Validation

The application includes comprehensive data validation:

### Built-in Validations
- **Required Fields**: Ensure all required columns are present
- **Data Types**: Validate data types match expected formats
- **Null Values**: Check for missing data and provide statistics
- **Duplicates**: Identify and report duplicate records
- **Format Validation**: Validate phone numbers, emails, URLs, etc.

### Custom Validation Rules
You can define custom validation rules in YAML format:

```yaml
validation:
  required_fields: ["name", "address", "phone"]
  data_types:
    name: "string"
    phone: "phone"
    email: "email"
    rating: "float"
  custom_rules:
    - field: "phone"
      pattern: "^\\+?[1-9]\\d{1,14}$"
    - field: "rating"
      min: 0
      max: 5
```

## 📈 Monitoring and Logging

### Logging Features
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Performance Tracking**: Automatic timing of operations
- **Scraping Statistics**: Track success rates and performance metrics
- **Log Rotation**: Automatic log file rotation to manage disk space

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General application information
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause application failure

## 🚀 Deployment

### Docker Deployment
```bash
# Build the Docker image
docker build -f deployment/Dockerfile -t google-maps-scraping .

# Run the container
docker run -v $(pwd)/data:/app/data google-maps-scraping import --csv data/raw/businesses.csv
```

### Production Deployment
1. Set environment variables for production
2. Configure logging for production environment
3. Set up monitoring and alerting
4. Configure backup strategies for data

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make your changes
5. Add tests for new functionality
6. Run the test suite
7. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters
- Add docstrings for all functions and classes
- Write comprehensive tests

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `docs/` directory
- Review the configuration examples

## 🔄 Roadmap

### Planned Features
- [ ] Google Maps scraping automation
- [ ] Advanced data visualization
- [ ] API endpoints for data access
- [ ] Real-time monitoring dashboard
- [ ] Machine learning data quality scoring
- [ ] Multi-language support
- [ ] Cloud deployment templates

### Version History
- **v1.0.0**: Initial release with data import and processing capabilities