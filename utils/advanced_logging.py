import os
import logging
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add color to console logs"""
    COLORS = {
        'DEBUG': '\033[94m',      # Blue
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[91;1m', # Bright Red
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            log_message = log_message.replace(record.levelname, colored_levelname, 1)
        return log_message

def setup_advanced_logging(log_level=logging.INFO, show_process_info=False):
    """
    Sets up advanced logging with color-coded console output and detailed file logging.
    
    Args:
        log_level: The logging level (default: logging.INFO)
        show_process_info: Whether to show process ID and thread info
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure log file name with date
    log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set log levels
    file_handler.setLevel(log_level)
    console_handler.setLevel(log_level)
    
    # Define log format based on detail preference
    if show_process_info:
        log_format = '%(asctime)s - %(levelname)s - [%(process)d:%(threadName)s] - %(filename)s:%(lineno)d - %(message)s'
    else:
        log_format = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    
    # Configure formatters
    file_formatter = logging.Formatter(log_format)
    console_formatter = ColoredFormatter(log_format)
    
    # Set formatters to handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log initial message
    logging.info("Advanced logging system initialized")
    return root_logger