"""
Logging utilities for BancaFiel backend
Provides structured logging for Lambda functions
"""
import logging
import json
from datetime import datetime


def setup_logger(name, level=logging.INFO):
    """
    Configure structured logging for Lambda functions.

    Args:
        name (str): Logger name (typically __name__)
        level: Logging level

    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create handler if not already exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_event(logger, event_type, data):
    """
    Log structured event data.

    Args:
        logger: Logger instance
        event_type (str): Type of event
        data (dict): Event data
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data
    }
    logger.info(json.dumps(log_entry))


def log_error(logger, error_type, error, context=None):
    """
    Log error with context.

    Args:
        logger: Logger instance
        error_type (str): Type of error
        error (Exception): Exception object
        context (dict): Additional context
    """
    error_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': error_type,
        'error_message': str(error),
        'error_class': error.__class__.__name__,
        'context': context or {}
    }
    logger.error(json.dumps(error_entry))
