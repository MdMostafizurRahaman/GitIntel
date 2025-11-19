"""
Logging utility module
"""

import logging
import logging.handlers
from pathlib import Path
from config.config import LOGGING_CONFIG

def setup_logger(name: str) -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    # Create logs directory
    log_dir = Path(LOGGING_CONFIG["file"]).parent
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_CONFIG["level"])
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOGGING_CONFIG["file"],
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Formatter
    formatter = logging.Formatter(LOGGING_CONFIG["format"])
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger(__name__)
