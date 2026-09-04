import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.cloud_logger.config import LoggerConfig

class LocalStorageManager:
    """Manages 100% local log custody via rotating JSONL files and SQLite database."""

    def __init__(self, config: LoggerConfig):
        self.config = config
        self.log_dir = config.log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.app_jsonl = self.log_dir / "app.jsonl"
        self.error_jsonl = self.log_dir / "error.jsonl"
        self.db_path = self.log_dir / "telemetry.db"

        self._lock = threading.Lock()
        if self.config.enable_local_db:
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite table and indices for telemetry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_number INTEGER,
                    message TEXT NOT NULL,
                    execution_time_ms REAL,
                    context_json TEXT,
                    traceback TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON telemetry_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_logs_level ON telemetry_logs(level);
                CREATE INDEX IF NOT EXISTS idx_logs_project ON telemetry_logs(project_name);
            """)
            conn.commit()

    def _rotate_if_needed(self, file_path: Path) -> None:
        """Rotate log file if it exceeds the maximum size limit."""
        if not file_path.exists():
            return
        try:
            if file_path.stat().st_size >= self.config.max_file_size_bytes:
                for i in range(self.config.backup_count - 1, 0, -1):
                    src = file_path.with_name(f"{file_path.stem}.{i}{file_path.suffix}")
                    dest = file_path.with_name(f"{file_path.stem}.{i+1}{file_path.suffix}")
                    if src.exists():
                        src.rename(dest)
                file_path.rename(file_path.with_name(f"{file_path.stem}.1{file_path.suffix}"))
        except Exception:
            pass

    def write_log(self, record: Dict[str, Any]) -> None:
        """Write structured log record to local JSONL and SQLite storage."""
        line = json.dumps(record, ensure_ascii=False) + "\n"

        with self._lock:
            # 1. Append to app.jsonl
            try:
                self._rotate_if_needed(self.app_jsonl)
                with open(self.app_jsonl, "a", encoding="utf-8") as f:
                    f.write(line)

                # If error or critical, duplicate to error.jsonl
                if record.get("level") in ("ERROR", "CRITICAL"):
                    self._rotate_if_needed(self.error_jsonl)
                    with open(self.error_jsonl, "a", encoding="utf-8") as ef:
                        ef.write(line)
            except Exception:
                pass

            # 2. Insert into local SQLite database
            if self.config.enable_local_db:
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO telemetry_logs (
                                timestamp, level, project_name, module, function,
                                line_number, message, execution_time_ms, context_json, traceback
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                record.get("timestamp"),
                                record.get("level"),
                                record.get("project_name"),
                                record.get("module"),
                                record.get("function"),
                                record.get("line_number"),
                                record.get("message"),
                                record.get("execution_time_ms"),
                                json.dumps(record.get("context", {}), ensure_ascii=False) if record.get("context") else None,
                                record.get("traceback"),
                            ),
                        )
                        conn.commit()
                except Exception:
                    pass

    def get_recent_logs(self, limit: int = 50, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent logs from local SQLite database."""
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if level:
                cursor.execute(
                    "SELECT * FROM telemetry_logs WHERE level = ? ORDER BY id DESC LIMIT ?",
                    (level.upper(), limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM telemetry_logs ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate local storage statistics."""
        if not self.db_path.exists():
            return {"total_logs": 0, "errors": 0, "db_size_bytes": 0}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry_logs")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM telemetry_logs WHERE level IN ('ERROR', 'CRITICAL')")
            errors = cursor.fetchone()[0]

            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "total_logs": total,
                "errors": errors,
                "db_size_bytes": db_size,
            }
