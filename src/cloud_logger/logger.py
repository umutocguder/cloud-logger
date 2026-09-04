import functools
import inspect
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from src.cloud_logger.config import LoggerConfig
from src.cloud_logger.google_exporter import GoogleCloudExporter
from src.cloud_logger.storage import LocalStorageManager

LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# ANSI Color codes for terminal output
COLOR_MAP = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[1;35m",# Bold Magenta
    "RESET": "\033[0m",
}

class CloudLogger:
    """High-performance structured logger with 100% local custody and Google Cloud streaming."""

    def __init__(self, project_name: str, log_dir: Optional[Path] = None):
        self.config = LoggerConfig.from_env(project_name, log_dir)
        self.storage = LocalStorageManager(self.config)
        self.exporter = GoogleCloudExporter(self.config)

    def _should_log(self, level: str) -> bool:
        """Check if message level meets configured threshold."""
        current_threshold = LEVEL_ORDER.get(self.config.log_level, 20)
        return LEVEL_ORDER.get(level, 20) >= current_threshold

    def _get_caller_info(self) -> Dict[str, Any]:
        """Inspect call stack to retrieve module, function name, and line number."""
        try:
            # Walk up 2 frames: [0] = _log, [1] = info/error/etc., [2] = caller
            frame = inspect.currentframe()
            for _ in range(3):
                if frame and frame.f_back:
                    frame = frame.f_back

            if frame:
                return {
                    "module": Path(frame.f_code.co_filename).stem,
                    "function": frame.f_code.co_name,
                    "line_number": frame.f_lineno,
                }
        except Exception:
            pass

        return {"module": "unknown", "function": "unknown", "line_number": 0}

    def _log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Any] = None,
        execution_time_ms: Optional[float] = None,
    ) -> None:
        """Core internal logging pipeline."""
        if not self._should_log(level):
            return

        now = datetime.utcnow().isoformat() + "Z"
        caller = self._get_caller_info()

        # Format exception traceback if provided
        tb_str = None
        if exc_info:
            if isinstance(exc_info, BaseException):
                tb_str = "".join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
            elif exc_info is True:
                tb_str = traceback.format_exc()

        record = {
            "timestamp": now,
            "level": level,
            "project_name": self.config.project_name,
            "module": caller["module"],
            "function": caller["function"],
            "line_number": caller["line_number"],
            "message": str(message),
            "execution_time_ms": round(execution_time_ms, 2) if execution_time_ms is not None else None,
            "context": context or {},
            "traceback": tb_str,
        }

        # 1. Console Output (if enabled)
        if self.config.enable_console:
            color = COLOR_MAP.get(level, "")
            reset = COLOR_MAP["RESET"]
            prefix = f"[{record['timestamp'][:19]}] [{color}{level:<8}{reset}] [{self.config.project_name}:{caller['module']}:{caller['function']}:{caller['line_number']}]"
            timing = f" ({record['execution_time_ms']}ms)" if record["execution_time_ms"] else ""
            print(f"{prefix} {message}{timing}", file=sys.stderr if level in ("ERROR", "CRITICAL") else sys.stdout)
            if tb_str:
                print(f"{color}{tb_str.strip()}{reset}", file=sys.stderr)

        # 2. Local Dual-Write Storage (100% Local Data Custody)
        self.storage.write_log(record)

        # 3. Asynchronous Google Cloud Dispatch
        self.exporter.enqueue(record)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("DEBUG", message, context=context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("INFO", message, context=context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("WARNING", message, context=context)

    def error(self, message: str, error: Optional[Any] = None, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("ERROR", message, context=context, exc_info=error)

    def critical(self, message: str, error: Optional[Any] = None, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("CRITICAL", message, context=context, exc_info=error)

    def exception(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error including active sys.exc_info() traceback."""
        self._log("ERROR", message, context=context, exc_info=sys.exc_info()[1] or True)

    def timed(self, name: Optional[str] = None) -> Callable:
        """Decorator to automatically measure and log function execution duration."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                action_name = name or func.__name__
                try:
                    result = func(*args, **kwargs)
                    duration = (time.perf_counter() - start) * 1000
                    self._log("INFO", f"Executed {action_name}", execution_time_ms=duration)
                    return result
                except Exception as e:
                    duration = (time.perf_counter() - start) * 1000
                    self._log("ERROR", f"Failed {action_name}: {e}", exc_info=e, execution_time_ms=duration)
                    raise e
            return wrapper
        return decorator
