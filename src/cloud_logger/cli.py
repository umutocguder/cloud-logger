import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List

def format_size(bytes_num: int) -> str:
    """Format bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(bytes_num) < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"

def find_log_files(base_dir: Path) -> List[Path]:
    """Find all local log files across projects in mycodespaces."""
    log_files = []
    if base_dir.exists():
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".jsonl", ".log")):
                    log_files.append(Path(root) / file)
    return log_files

def cmd_tail(args):
    """Live follow local log files."""
    log_file = Path(args.file) if args.file else Path.cwd() / "logs" / "app.jsonl"
    if not log_file.exists():
        print(f"[-] Log file not found: {log_file}")
        return

    print(f"[*] Following {log_file} (Press Ctrl+C to stop)...")
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Move to end
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    try:
                        record = json.loads(line)
                        level = record.get("level", "INFO")
                        time_str = record.get("timestamp", "")[:19]
                        proj = record.get("project_name", "")
                        msg = record.get("message", "")
                        if args.errors_only and level not in ("ERROR", "CRITICAL"):
                            continue
                        print(f"[{time_str}] [{level:<8}] [{proj}] {msg}")
                    except Exception:
                        print(line.strip())
                else:
                    time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[*] Stopped.")

def cmd_errors(args):
    """Show recent errors across local projects."""
    projects_dir = Path("/Users/umut/mycodespaces")
    limit = args.limit or 20
    errors = []

    for path in projects_dir.glob("*/logs/error.jsonl"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        errors.append(json.loads(line))
        except Exception:
            pass

    errors.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    recent = errors[:limit]

    print("\n" + "=" * 60)
    print(f"       RECENT LOCAL ERRORS ({len(recent)} found)")
    print("=" * 60)

    if not recent:
        print("  [+] No local errors recorded! System is healthy.")
    else:
        for err in recent:
            ts = err.get("timestamp", "")[:19]
            proj = err.get("project_name", "unknown")
            msg = err.get("message", "")
            func = f"{err.get('module', '')}.{err.get('function', '')}:{err.get('line_number', '')}"
            print(f"\n  [{ts}] [{err.get('level')}] Project: {proj} ({func})")
            print(f"  Message: {msg}")
            if err.get("traceback"):
                print("  Traceback:")
                for tb_line in err["traceback"].strip().split("\n")[-4:]:
                    print(f"    {tb_line}")
    print("=" * 60 + "\n")

def cmd_stats(args):
    """Display aggregate log storage and counts across all personal projects."""
    projects_dir = Path("/Users/umut/mycodespaces")
    total_files = 0
    total_bytes = 0
    projects_found = []

    for proj in projects_dir.iterdir():
        if proj.is_dir():
            log_dir = proj / "logs"
            if log_dir.exists():
                proj_size = sum(f.stat().st_size for f in log_dir.glob("*") if f.is_file())
                total_bytes += proj_size
                total_files += len(list(log_dir.glob("*")))
                projects_found.append((proj.name, proj_size))

    print("\n" + "=" * 50)
    print("     LOCAL TELEMETRY & LOG CUSTODY STATS")
    print("=" * 50)
    print(f" Monitored Projects: {len(projects_found)}")
    print(f" Total Log Files:    {total_files}")
    print(f" Total Storage Used: {format_size(total_bytes)}")
    print("-" * 50)
    for name, size in sorted(projects_found, key=lambda x: x[1], reverse=True):
        print(f"  - {name:<25} {format_size(size)}")
    print("=" * 50 + "\n")

def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for log-cli."""
    parser = argparse.ArgumentParser(
        prog="log-cli",
        description="Local telemetry inspector and log manager for personal projects.",
    )
    sub = parser.add_subparsers(dest="command", help="Command to execute")

    # tail
    t_p = sub.add_parser("tail", help="Follow log file in real time")
    t_p.add_argument("--file", help="Specific log file path")
    t_p.add_argument("--errors-only", action="store_true", help="Only show errors")

    # errors
    e_p = sub.add_parser("errors", help="List recent errors across projects")
    e_p.add_argument("--limit", type=int, default=20, help="Max entries to show")

    # stats
    sub.add_parser("stats", help="Show local storage metrics and counts")

    return parser
