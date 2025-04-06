# utils/helpers.py
import os
import logging
from datetime import datetime

def setup_logging():
    """Mengatur konfigurasi logging."""
    os.makedirs('logs', exist_ok=True)
    log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(log_file), logging.StreamHandler()])