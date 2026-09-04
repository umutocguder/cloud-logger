#!/usr/bin/env python3
"""
Cloud Logger CLI Entrypoint.
Inspect, tail, and aggregate local logs across all personal projects.
"""

import sys
from src.cloud_logger.cli import (
    build_parser,
    cmd_tail,
    cmd_errors,
    cmd_stats,
)

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        # Default to stats if no command provided
        cmd_stats(args)
        sys.exit(0)

    dispatch = {
        "tail": cmd_tail,
        "errors": cmd_errors,
        "stats": cmd_stats,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
