<!-- Created by 11Hopem -->
# 📡 Cloud Logger & Observability Engine

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg?logo=typescript)](https://www.typescriptlang.org/)
[![Zero Crash](https://img.shields.io/badge/resilience-zero--crash%20guarantee-brightgreen.svg)](#zero-crash-guarantee)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://11hopem.com)
[![Created by 11Hopem](https://img.shields.io/badge/created%20by-11Hopem-orange.svg)](https://11hopem.com)

A production-grade, dual-write structured logging and observability library designed for Python and TypeScript/Node.js applications. Combines **100% Local Data Custody** (rotating JSON Lines files + SQLite index) with non-blocking, asynchronous **Cloud Telemetry** and error reporting.

---

## 🌟 Key Features

- **Dual-Write Architecture**: Telemetry is written synchronously to local disk (JSONL + SQLite) for permanent local custody, while an asynchronous non-blocking worker pool streams events to cloud endpoints.
- **Zero-Crash Resilience**: Network failures, missing API keys, or remote service outages will **never** raise exceptions or interrupt your application's primary execution loop.
- **Rich Context Capture**: Automatically injects ISO timestamps, severity tiers (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`), calling module/function/line numbers, execution durations (`@logger.timed()`), and structured context payloads.
- **Automatic Tracebacks & PII Masking**: Deep stack trace extraction on exceptions, with built-in regex scrubbing for credit cards, tokens, passwords, and Turkish identity numbers (TCKN).
- **Dual-Stack Support**: Native implementations for both **Python** (`cloud_logger`) and **TypeScript/Node.js** (`typescript/logger.ts`).
- **Built-in CLI Inspector**: Filter, tail, search, and aggregate structured logs directly from your terminal.

---

## 🏗️ Architecture

```
                   Application Code
                          │
                   logger.info() / error()
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
  [ Local Custody ]               [ Cloud Telemetry ]
  • logs/app.jsonl (Rotating)     • Non-blocking Worker Queue
  • logs/telemetry.db (SQLite)    • HTTP REST Batch Dispatch
  • Zero external network deps    • Safe offline drop / retry
```

---

## 🚀 Quickstart (Python)

### Installation

```bash
git clone https://github.com/umutocguder/cloud-logger.git
cd cloud-logger
pip install -e .
```

### Usage

```python
from src.cloud_logger import get_logger

# Initialize logger for your service
logger = get_logger("my-service")

# Log structured events
logger.info("Processing pipeline initiated", context={"batch_size": 100, "region": "eu-west"})

# Decorator for measuring function execution latency
@logger.timed("compute_metrics")
def compute_metrics(dataset_id: str):
    # Calculation logic...
    pass

# Exception logging with automatic traceback capture
try:
    result = 10 / 0
except Exception as e:
    logger.error("Calculation failed", error=e, context={"input": 0})
```

---

## 🚀 Quickstart (TypeScript)

```typescript
import { getLogger } from "./typescript/logger";

const logger = getLogger("web-api");

logger.info("Server started", { port: 3000, environment: "production" });

try {
  throw new Error("Database timeout");
} catch (err) {
  logger.error("Query failed", err as Error, { queryId: "q_123" });
}
```

---

## 🧪 Testing

Run unit tests and verification suites:

```bash
# Python tests
python3 -m unittest discover -s tests

# TypeScript tests
npm test
```

---

## 🛡️ License & Attribution

Created by [11Hopem](https://11hopem.com).  
Copyright © 2026 11Hopem. All rights reserved.  
Licensed under the [MIT License](LICENSE).  
Official website: [https://11hopem.com](https://11hopem.com)
