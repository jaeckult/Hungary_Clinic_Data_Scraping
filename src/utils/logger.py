"""
Advanced logging utilities for the Google Maps scraping project.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredLogger:
    """Structured logging with JSON output and performance tracking."""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.name = name
        self.log_file = log_file
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> structlog.BoundLogger:
        """Setup structured logger with processors."""
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ]
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger(self.name)
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with additional context."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with additional context."""
        self.logger.critical(message, **kwargs)


class PerformanceLogger:
    """Logger for tracking performance metrics."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.start_times: Dict[str, datetime] = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = datetime.now()
        self.logger.info(f"Started {operation}")
    
    def end_timer(self, operation: str, **context):
        """End timing an operation and log the duration."""
        if operation not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return
        
        start_time = self.start_times[operation]
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(
            f"Completed {operation}",
            duration_seconds=duration,
            operation=operation,
            **context
        )
        
        del self.start_times[operation]


class ScrapingLogger:
    """Specialized logger for scraping operations."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_records': 0,
            'start_time': datetime.now()
        }
    
    def log_request(self, url: str, status_code: int, response_time: float, **context):
        """Log a scraping request."""
        self.stats['total_requests'] += 1
        
        if 200 <= status_code < 300:
            self.stats['successful_requests'] += 1
            self.logger.info(
                "Scraping request successful",
                url=url,
                status_code=status_code,
                response_time=response_time,
                **context
            )
        else:
            self.stats['failed_requests'] += 1
            self.logger.error(
                "Scraping request failed",
                url=url,
                status_code=status_code,
                response_time=response_time,
                **context
            )
    
    def log_records_processed(self, count: int, source: str):
        """Log processed records."""
        self.stats['total_records'] += count
        self.logger.info(
            f"Processed {count} records from {source}",
            records_processed=count,
            source=source,
            total_records=self.stats['total_records']
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        success_rate = (
            self.stats['successful_requests'] / self.stats['total_requests']
            if self.stats['total_requests'] > 0 else 0
        )
        
        return {
            **self.stats,
            'duration_seconds': duration,
            'success_rate': success_rate,
            'requests_per_minute': self.stats['total_requests'] / (duration / 60) if duration > 0 else 0
        }
    
    def log_summary(self):
        """Log a summary of scraping operations."""
        stats = self.get_stats()
        self.logger.info(
            "Scraping session summary",
            **stats
        )


def setup_logging(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    max_file_size: str = "10MB",
    backup_count: int = 5
) -> StructuredLogger:
    """Setup logging with file and console handlers."""
    
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create structured logger
    logger = StructuredLogger(name, log_file)
    
    # Setup handlers
    handlers = []
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=parse_size(max_file_size),
            backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handlers.append(file_handler)
    
    # Console handler with colors
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handlers.append(console_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers and add new ones
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    return logger


def parse_size(size_str: str) -> int:
    """Parse size string (e.g., '10MB') to bytes."""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


# Convenience functions
def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def get_scraping_logger(name: str) -> ScrapingLogger:
    """Get a scraping logger instance."""
    return ScrapingLogger(StructuredLogger(name))


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger instance."""
    return PerformanceLogger(StructuredLogger(name))
