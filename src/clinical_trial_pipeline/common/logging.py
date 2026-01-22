"""Basic logging configuration."""

import logging
import sys

DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_LEVEL = logging.INFO

_configured = False


def setup_logging(level: int = DEFAULT_LEVEL, format_string: str = DEFAULT_FORMAT) -> None:
    """Configure basic logging for the application.

    Args:
        level: Logging level (default: INFO)
        format_string: Log message format
    """
    global _configured

    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format_string))

    root_logger = logging.getLogger("clinical_trial_pipeline")
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
