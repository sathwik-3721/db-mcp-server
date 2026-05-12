import logging
from src.db_mcp.core.config import config

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
        
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    
    handler = logging.StreamHandler()
    
    if config.LOG_FORMAT == "json":
        try:
            from pythonjsonlogger import jsonlogger
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s'
            )
            handler.setFormatter(formatter)
        except ImportError:
            # Fallback if jsonlogger not installed
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.warning("python-json-logger not installed. Falling back to text format.")
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        
    logger.addHandler(handler)
    # Prevent propagation to root logger to avoid duplicate logs in some setups
    logger.propagate = False 
    
    return logger
