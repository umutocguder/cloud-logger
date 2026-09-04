# Cloud Logger & Observability Engine

A dual-write, zero-crash structured logging library for personal projects with **100% Local Data Custody** (rotating JSON Lines + SQLite) and asynchronous **Google Cloud Observability** (Google Cloud Logging & Error Reporting).

---

## 🌟 Key Features

- **Extensive Structured Logging**: Automatic capture of timestamps, severity levels, module names, functions, line numbers, execution durations (`@logger.timed()`), context dictionaries, and full tracebacks.
- **100% Local Data Custody**: Logs are immediately written to local disk (`logs/app.jsonl`, `logs/error.jsonl`) and local SQLite (`logs/telemetry.db`). You maintain full, permanent possession of all telemetry data locally.
- **Google Cloud Observability**: Non-blocking background worker that streams logs to Google Cloud Logging API. Critical errors (`ERROR`, `CRITICAL`) trigger Google Cloud Error Reporting for immediate mobile/web console alerts.
- **Zero-Crash Resilience**: If Google credentials are missing or the system is offline, logging operates purely in local custody mode without throwing exceptions or blocking the host application.
- **Dual-Stack Support**: Includes Python library (`cloud_logger`) and TypeScript client (`typescript/logger.ts`).
- **Local Inspector CLI**: Query, tail, and search logs across all personal projects using `main.py` / `log-cli`.

---

## 🚀 Quick Start (Python)

### 1. Basic Usage

```python
from src.cloud_logger import get_logger

# Initialize logger for your project
logger = get_logger("google-photos-backup")

# Standard log messages with custom structured context
logger.info("Sync started", context={"batch_size": 50, "workers": 5})

# Automatic execution timing decorator
@logger.timed("process_media")
def process_media(item_id: str):
    # your logic here
    pass

# Error reporting (automatically captured in logs/error.jsonl & Google Cloud Error Reporting)
try:
    1 / 0
except Exception as err:
    logger.error("Calculation failed", error=err, context={"user_id": 42})
```

---

## 💻 Quick Start (TypeScript / Node.js)

```typescript
import { createLogger } from './typescript/logger';

const logger = createLogger('boutique-platform');

logger.info('Order received', { orderId: 'ord_123', amount: 450 });

try {
  throw new Error('Database connection timed out');
} catch (err) {
  logger.error('Failed to query inventory', err, { retryCount: 3 });
}
```

---

## ☁️ Google Cloud Setup (Optional)

To stream logs directly to your Google Cloud Console:

1. Create a Google Cloud Project (or use an existing one).
2. Enable the **Cloud Logging API** & **Error Reporting API**:
   ```bash
   gcloud services enable logging.googleapis.com clouderrorreporting.googleapis.com
   ```
3. Create a Service Account with the role **Logs Writer** & **Error Reporting Writer**.
4. Download the JSON key and set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
   export GCP_PROJECT_ID="your-project-id"
   ```
*If credentials are not supplied, logs continue writing safely to local disk and SQLite.*

---

## 🔍 Local Log Inspector CLI

```bash
# View aggregate log storage and project counts across all ~/mycodespaces
python3 main.py stats

# View recent errors and tracebacks across all projects
python3 main.py errors --limit 10

# Live follow a log file
python3 main.py tail --file logs/app.jsonl
```

---

## 🔒 Confidentiality Notice

- **Personal Projects Only**: This library is strictly configured for personal repositories under `~/mycodespaces/*`.
- **Company Data Isolation**: Company projects (`/Users/umut/intetra/`) are strictly excluded and must never stream telemetry to external endpoints.
