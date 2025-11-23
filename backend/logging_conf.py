from __future__ import annotations

import logging
import re
import traceback
from typing import Any


SENSITIVE_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",  # clés API type sk-...
    r"Bearer\s+[A-Za-z0-9\.\-_]+",  # tokens Bearer
]


def _mask_sensitive(text: str) -> str:
    masked = text
    for pattern in SENSITIVE_PATTERNS:
        masked = re.sub(pattern, "***REDACTED***", masked)
    return masked


class PIIFilter(logging.Filter):
    """Filtre qui masque les éléments sensibles dans les logs."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        if isinstance(record.msg, str):
            record.msg = _mask_sensitive(record.msg)
        if record.args:
            new_args: list[Any] = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(_mask_sensitive(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure le logging global de l'application."""
    logging_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    root_logger = logging.getLogger()
    root_logger.addFilter(PIIFilter())


def log_exception(exc: BaseException, logger_name: str = "fmp") -> None:
    """Log une exception avec stacktrace."""
    logger = logging.getLogger(logger_name)
    logger.error("Exception: %s", exc)
    logger.debug("Traceback:\n%s", traceback.format_exc())
