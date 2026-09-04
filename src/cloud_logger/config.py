import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class LoggerConfig:
    """Configuration settings for CloudLogger."""
    project_name: str
    log_dir: Path
    log_level: str = "INFO"
    gcp_project_id: Optional[str] = None
    credentials_path: Optional[str] = None
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB per file
    backup_count: int = 5
    enable_console: bool = True
    enable_local_db: bool = True
    enable_google_cloud: bool = True

    @classmethod
    def from_env(cls, project_name: str, log_dir: Optional[Path] = None) -> "LoggerConfig":
        """Load configuration from environment variables with sensible defaults."""
        target_dir = log_dir or (Path.cwd() / "logs")
        target_dir.mkdir(parents=True, exist_ok=True)

        gcp_project = (
            os.getenv("GCP_PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCLOUD_PROJECT")
        )

        creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds:
            # Check default candidate paths
            candidates = [
                Path.cwd() / "service_account.json",
                Path.home() / ".config" / "gcloud" / "application_default_credentials.json",
            ]
            for c in candidates:
                if c.exists():
                    creds = str(c)
                    break

        return cls(
            project_name=project_name,
            log_dir=target_dir,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            gcp_project_id=gcp_project,
            credentials_path=creds,
            enable_console=os.getenv("LOG_CONSOLE", "true").lower() in ("true", "1", "yes"),
            enable_local_db=os.getenv("LOG_SQLITE", "true").lower() in ("true", "1", "yes"),
            enable_google_cloud=os.getenv("LOG_GCP", "true").lower() in ("true", "1", "yes"),
        )
