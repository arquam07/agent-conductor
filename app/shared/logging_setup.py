"""Logging setup. Honors --debug: adds a timestamped file handler so each
flowchart block can log its step. Block names here match the diagram labels."""
import logging
import sys
from datetime import datetime, timezone


def setup_logging(debug: bool = False, component: str = "app") -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger(component)
    logger.setLevel(level)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    # Console (stdout so K8s captures it)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # Debug: also write to a timestamped file
    if debug:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        fh = logging.FileHandler(f"{component}_debug_{ts}.log")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.debug("debug logging enabled")

    return logger


def log_block(logger: logging.Logger, block: str, msg: str = "") -> None:
    """Log one flowchart block. `block` should match a diagram label."""
    logger.debug("BLOCK %s | %s", block, msg)