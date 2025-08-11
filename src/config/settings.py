"""
Configuration management for the Google Maps scraping project.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging


@dataclass
class AppConfig:
    """Application configuration."""
    name: str
    version: str
    environment: str
    debug: bool


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    format: str
    file: str
    max_size: str
    backup_count: int
    console_output: bool


@dataclass
class DataConfig:
    """Data processing configuration."""
    encoding: str
    chunk_size: int
    max_rows: Optional[int]
    backup_original: bool
    compression: Optional[str]


@dataclass
class ScrapingConfig:
    """Scraping configuration."""
    base_url: str
    search_delay: float
    max_retries: int
    timeout: int
    user_agent: str
    headless: bool
    proxy_enabled: bool
    proxy_list: list


@dataclass
class RateLimitingConfig:
    """Rate limiting configuration."""
    requests_per_minute: int
    requests_per_hour: int
    cooldown_period: int


@dataclass
class ValidationConfig:
    """Data validation configuration."""
    required_fields: list
    optional_fields: list
    data_types: Dict[str, str]


class Settings:
    """Main settings class that loads and manages configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()
        self._setup_logging()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "config" / "settings.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables
            config = self._override_with_env_vars(config)
            
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _override_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables."""
        env_mappings = {
            'GOOGLE_MAPS_API_KEY': ('security', 'api_keys', 'google_maps'),
            'PROXY_SERVICE_KEY': ('security', 'api_keys', 'proxy_service'),
            'LOG_LEVEL': ('logging', 'level'),
            'ENVIRONMENT': ('app', 'environment'),
            'DEBUG': ('app', 'debug'),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config, config_path, env_value)
        
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], path: tuple, value: Any):
        """Set a nested value in the configuration dictionary."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        log_config = self.logging
        
        # Create logs directory if it doesn't exist
        log_file_path = Path(log_config.file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config.level.upper()),
            format=log_config.format,
            handlers=[
                logging.FileHandler(log_config.file),
                logging.StreamHandler() if log_config.console_output else logging.NullHandler()
            ]
        )
    
    @property
    def app(self) -> AppConfig:
        """Get application configuration."""
        app_config = self._config.get('app', {})
        return AppConfig(
            name=app_config.get('name', 'Google Maps Scraping'),
            version=app_config.get('version', '1.0.0'),
            environment=app_config.get('environment', 'development'),
            debug=app_config.get('debug', False)
        )
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        log_config = self._config.get('logging', {})
        return LoggingConfig(
            level=log_config.get('level', 'INFO'),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file=log_config.get('file', 'logs/app.log'),
            max_size=log_config.get('max_size', '10MB'),
            backup_count=log_config.get('backup_count', 5),
            console_output=log_config.get('console_output', True)
        )
    
    @property
    def data(self) -> DataConfig:
        """Get data processing configuration."""
        data_config = self._config.get('data', {})
        return DataConfig(
            encoding=data_config.get('encoding', 'utf-8'),
            chunk_size=data_config.get('chunk_size', 10000),
            max_rows=data_config.get('max_rows'),
            backup_original=data_config.get('backup_original', True),
            compression=data_config.get('compression')
        )
    
    @property
    def scraping(self) -> ScrapingConfig:
        """Get scraping configuration."""
        scraping_config = self._config.get('scraping', {}).get('google_maps', {})
        return ScrapingConfig(
            base_url=scraping_config.get('base_url', 'https://www.google.com/maps'),
            search_delay=scraping_config.get('search_delay', 2.0),
            max_retries=scraping_config.get('max_retries', 3),
            timeout=scraping_config.get('timeout', 30),
            user_agent=scraping_config.get('user_agent', 'Mozilla/5.0'),
            headless=scraping_config.get('headless', True),
            proxy_enabled=scraping_config.get('proxy_enabled', False),
            proxy_list=scraping_config.get('proxy_list', [])
        )
    
    @property
    def rate_limiting(self) -> RateLimitingConfig:
        """Get rate limiting configuration."""
        rate_config = self._config.get('scraping', {}).get('rate_limiting', {})
        return RateLimitingConfig(
            requests_per_minute=rate_config.get('requests_per_minute', 30),
            requests_per_hour=rate_config.get('requests_per_hour', 1000),
            cooldown_period=rate_config.get('cooldown_period', 60)
        )
    
    @property
    def validation(self) -> ValidationConfig:
        """Get validation configuration."""
        validation_config = self._config.get('validation', {})
        return ValidationConfig(
            required_fields=validation_config.get('required_fields', []),
            optional_fields=validation_config.get('optional_fields', []),
            data_types=validation_config.get('data_types', {})
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


# Global settings instance
settings = Settings()
