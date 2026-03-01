#!/usr/bin/env python3
"""
Instinct CLI - Main entry point for Instinct-Learning Plugin.

This script provides a command-line interface for managing learned instincts,
including viewing status, importing/exporting, pruning, and analyzing confidence decay.

Available Commands:
  status   - Show all learned instincts with confidence scores
  import   - Import instincts from file or URL
  export   - Export instincts to file or stdout
  prune    - Enforce max instincts limit by archiving low-confidence ones
  decay    - Show effective confidence after time-based decay

Usage Examples:
    # View all instincts
    python3 instinct_cli.py status

    # Export to file
    python3 instinct_cli.py export --output my-instincts.md

    # Import from URL
    python3 instinct_cli.py import https://example.com/instincts.md

    # Prune low-confidence instincts (dry-run first)
    python3 instinct_cli.py prune --dry-run

    # Show confidence decay analysis
    python3 instinct_cli.py decay

Note: Use /instinct:analyze command to dispatch the observer agent
for AI-based pattern detection from observations.
"""

import sys

from cli_parser import create_parser, parse_args

from commands import cmd_decay, cmd_export, cmd_import, cmd_prune, cmd_status


def main() -> int:
    """Main CLI entry point.

    This function parses command-line arguments and routes to the
    appropriate command handler. If no command is specified or an invalid
    command is provided, help text is displayed.

    Returns:
        0 on successful command execution
        1 on error or when showing help

    Command Routing:
        status   -> cmd_status
        import   -> cmd_import
        export   -> cmd_export
        prune    -> cmd_prune
        decay    -> cmd_decay
        (no command) -> show help and return 1
    """
    args = parse_args()

    if args.command == "status":
        return cmd_status(args)
    if args.command == "import":
        return cmd_import(args)
    if args.command == "export":
        return cmd_export(args)
    if args.command == "prune":
        return cmd_prune(args)
    if args.command == "decay":
        return cmd_decay(args)
    # No command specified, show help
    parser = create_parser()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
