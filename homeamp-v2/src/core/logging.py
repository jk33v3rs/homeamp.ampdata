"""HomeAMP V2.0 - Structured logging with audit trail support."""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from homeamp_v2.core.config import get_settings

# Global logger instance
_logger: logging.Logger | None = None


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def get_logger(name: str = "homeamp") -> logging.Logger:
    """Get or create logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return logging.getLogger(name)


def setup_logging() -> logging.Logger:
    """Configure logging with file and console handlers."""
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("homeamp")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    if settings.log_format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))

    logger.addHandler(console_handler)

    # File handler
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        settings.log_file, maxBytes=settings.log_max_bytes, backupCount=settings.log_backup_count
    )
    file_handler.setLevel(logging.DEBUG)

    if settings.log_format == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))

    logger.addHandler(file_handler)

    return logger


def audit_log(action: str, entity_type: str, entity_id: int | str, user: str, details: dict[str, Any] | None = None):
    """Log an audit trail entry."""
    logger = get_logger("homeamp.audit")
    audit_data = {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user": user,
        "details": details or {},
    }
    logger.info(f"AUDIT: {action} {entity_type} {entity_id} by {user}", extra={"audit": audit_data})
