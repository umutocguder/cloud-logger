# AGENTS.md — Cloud Logger & Observability Engine Guidelines

This document defines the architectural rules, coding standards, and operational guidelines for the **Cloud Logger** project (`cloud-logger`). All AI agents (Antigravity, Claude, Cursor) and human contributors must strictly follow these instructions.

---

## 1. Project Overview & Architecture

`cloud-logger` is a unified, production-grade telemetry and structured logging library designed for all personal projects in `~/mycodespaces/*`. It provides:
1. **Extensive Structured Logging**: Automatic capture of timestamps, log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`), project name, module, function name, execution duration, custom context dictionaries, and full exception tracebacks.
2. **100% Local Data Custody (Dual-Write)**:
   - Synchronous/fast local write to rotating JSON Lines files (`logs/app.jsonl`, `logs/error.jsonl`).
   - Local SQLite database logging (`logs/telemetry.db`) enabling rapid structured queries and analytics.
   - All log data remains permanently under the user's local custody.
3. **Google Cloud Observability (Async Background Dispatch)**:
   - Non-blocking background worker thread that streams logs to Google Cloud Logging API and Google Cloud Error Reporting.
   - High-priority error alerting: Any `ERROR` or `CRITICAL` log surfaces immediately in the Google Cloud Console / Error Reporting dashboard.
4. **Zero-Crash Resilience**:
   - If Google Cloud credentials are not present or the machine is offline, the logger gracefully continues writing to local files/database without impacting the host application.
5. **Dual-Stack Support**:
   - Python module (`cloud_logger`) with decorator support (`@logger.timed()`).
   - TypeScript module (`typescript/logger.ts`) for Node.js / Next.js projects.
   - Local log viewer CLI (`log-cli`) to tail, inspect, and search logs across all personal projects.

---

## 2. Mandatory Coding Standards (STRICT ENGLISH RULE)

1. **Source Code**:
   - Variable names, functions, classes, methods, dataclasses/models, type hints, and comments **MUST ALWAYS BE IN ENGLISH**.
2. **Commit Messages**:
   - All git commit messages must be in English following the Conventional Commits specification (`feat: ...`, `fix: ...`, `chore: ...`, `refactor: ...`).
3. **UI Text**:
   - CLI outputs and console text may include bilingual or Turkish explanations for the user, but the code layer must be 100% English.

---

## 3. Directory Layout

```text
cloud-logger/
├── AGENTS.md                  # Project rules & architecture
├── CLAUDE.md                  # Claude Code entrypoint (@AGENTS.md)
├── WORKLOG.md                 # AI handoff changelog
├── README.md                  # Setup & usage documentation
├── .gitignore                 # Secrets & ignore list
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Packaging configuration
│
├── src/
│   └── cloud_logger/
│       ├── __init__.py        # Package public interface (get_logger, CloudLogger)
│       ├── config.py          # Logger configuration & environment variables
│       ├── storage.py         # Local rotating JSONL & SQLite dual-writer
│       ├── google_exporter.py # Async worker streaming to Google Cloud Logging & Error Reporting
│       ├── logger.py          # High-level structured logger & decorators
│       └── cli.py             # Log inspector CLI tool (tail, errors, search)
│
├── typescript/
│   └── logger.ts              # TypeScript dual-write logger for Node.js / Next.js
│
└── main.py                    # CLI entrypoint for log-cli
```

---

## 4. Confidentiality & Security

- **Strict Personal Scope**: This library is exclusively for personal projects under `~/mycodespaces/*`. It must NEVER be used to stream company code or data (`/Users/umut/intetra/`).
- **Secrets Isolation**: Google service account keys and API tokens are strictly excluded by `.gitignore`.
- **Git Author**: All commits must use `Umut Öçgüder <umutocgdr@gmail.com>`.
- **Private Repository**: Hosted privately at `https://github.com/umutocguder/cloud-logger`.
