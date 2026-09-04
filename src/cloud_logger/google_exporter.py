import atexit
import json
import queue
import threading
import time
from typing import Any, Dict, Optional
from src.cloud_logger.config import LoggerConfig

class GoogleCloudExporter:
    """Asynchronous background worker streaming logs to Google Cloud Logging & Error Reporting."""

    def __init__(self, config: LoggerConfig):
        self.config = config
        self.queue: queue.Queue = queue.Queue(maxsize=10000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._gcp_client = None
        self._error_client = None
        self._initialized = False

        if self.config.enable_google_cloud:
            self._init_clients()
            self._worker_thread.start()
            atexit.register(self.shutdown)

    def _init_clients(self) -> None:
        """Attempt to initialize official Google Cloud SDK clients if installed and configured."""
        try:
            from google.cloud import error_reporting, logging as gcp_logging
            
            project = self.config.gcp_project_id
            if self.config.credentials_path:
                self._gcp_client = gcp_logging.Client.from_service_account_json(
                    self.config.credentials_path, project=project
                )
                self._error_client = error_reporting.Client.from_service_account_json(
                    self.config.credentials_path, project=project
                )
            else:
                self._gcp_client = gcp_logging.Client(project=project)
                self._error_client = error_reporting.Client(project=project)

            self._logger = self._gcp_client.logger(self.config.project_name)
            self._initialized = True
        except Exception:
            # Silent fallback: zero crash guarantee when credentials or SDK are not yet set
            self._initialized = False

    def enqueue(self, record: Dict[str, Any]) -> None:
        """Add log record to asynchronous dispatch queue."""
        if not self.config.enable_google_cloud or not self._initialized:
            return
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            pass  # Drop oldest or ignore to prevent blocking host process

    def _process_queue(self) -> None:
        """Worker loop reading queue and dispatching to Google Cloud Logging."""
        while not self._stop_event.is_set():
            try:
                record = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                self._dispatch_to_gcp(record)
            except Exception:
                pass  # Zero-crash policy
            finally:
                self.queue.task_done()

    def _dispatch_to_gcp(self, record: Dict[str, Any]) -> None:
        """Send record to Google Cloud Logging and Google Cloud Error Reporting."""
        if not self._initialized or not self._logger:
            return

        level = record.get("level", "INFO")
        message = record.get("message", "")
        payload = {
            "project": record.get("project_name"),
            "module": record.get("module"),
            "function": record.get("function"),
            "line": record.get("line_number"),
            "execution_time_ms": record.get("execution_time_ms"),
            "context": record.get("context", {}),
            "traceback": record.get("traceback"),
        }

        # Map to Google Cloud severity
        severity_map = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }
        severity = severity_map.get(level, "DEFAULT")

        # 1. Dispatch to Google Cloud Logging
        self._logger.log_struct(
            payload,
            severity=severity,
            labels={"project_name": record.get("project_name", "unknown")},
        )

        # 2. Dispatch critical errors to Google Cloud Error Reporting
        if level in ("ERROR", "CRITICAL") and self._error_client:
            try:
                self._error_client.report(
                    message=f"{message}\n{record.get('traceback') or ''}",
                    service=record.get("project_name"),
                )
            except Exception:
                pass

    def shutdown(self, timeout: float = 2.0) -> None:
        """Flush remaining items and stop worker thread."""
        self._stop_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
