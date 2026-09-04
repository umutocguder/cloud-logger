"""
Cloud Logger - Structured logging with 100% local custody and Google Cloud Observability.
"""

from pathlib import Path
from typing import Dict, Optional

from src.cloud_logger.config import LoggerConfig
from src.cloud_logger.logger import CloudLogger

__version__ = "0.1.0"

_LOGGERS: Dict[str, CloudLogger] = {}

def get_logger(project_name: str, log_dir: Optional[Path] = None) -> CloudLogger:
    """
    Retrieve or create a singleton CloudLogger instance for a specific project.
    
    Example:
        from cloud_logger import get_logger
        logger = get_logger("google-photos-backup")
        logger.info("Starting sync...", context={"batch_size": 50})
    """
    key = f"{project_name}:{log_dir}"
    if key not in _LOGGERS:
        _LOGGERS[key] = CloudLogger(project_name=project_name, log_dir=log_dir)
    return _LOGGERS[key]

__all__ = ["get_logger", "CloudLogger", "LoggerConfig"]
