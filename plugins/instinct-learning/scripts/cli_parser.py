"""
CLI argument parser for Instinct CLI.

This module provides argument parsing and configuration for all CLI commands.
It defines the command-line interface structure, argument specifications, and
help text.

Command Structure:
    instinct_cli.py <command> [command-specific-options]

Available Commands:
    status   - Display all learned instincts
    import   - Import instincts from file or URL
    export   - Export instincts to file
    prune    - Enforce max instincts limit
    decay    - Show confidence decay analysis

Each command has its own set of arguments and options as defined in
create_parser().

Example:
    >>> args = parse_args(['status', '--domain', 'testing'])
    >>> args.command
    'status'
    >>> args.domain
    'testing'
"""

import argparse
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser.

    Creates the main argument parser and adds subparsers for each command
    with their specific arguments and options.

    Returns:
        Configured ArgumentParser instance with all subcommands.

    Note:
        Each subparser is created but parsing is deferred until parse_args()
        is called. This allows for programmatic usage of the parser.
    """
    parser = argparse.ArgumentParser(description="Instinct CLI for Instinct-Learning Plugin")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    _ = subparsers.add_parser("status", help="Show instinct status")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import instincts")
    import_parser.add_argument("source", help="File path or URL")
    import_parser.add_argument("--dry-run", action="store_true", help="Preview without importing")
    import_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    import_parser.add_argument("--min-confidence", type=float, help="Minimum confidence threshold")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export instincts")
    export_parser.add_argument("--output", "-o", help="Output file")
    export_parser.add_argument("--domain", help="Filter by domain")
    export_parser.add_argument("--min-confidence", type=float, help="Minimum confidence")

    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Enforce max instincts limit")
    prune_parser.add_argument("--max-instincts", type=int, help="Maximum instincts to keep")
    prune_parser.add_argument("--dry-run", action="store_true", help="Preview without archiving")

    # Decay command
    decay_parser = subparsers.add_parser("decay", help="Show effective confidence after decay")
    decay_parser.add_argument("--decay-rate", type=float, help="Weekly decay rate")

    return parser


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    This function creates the parser and parses the provided argument list.
    If no arguments are provided, it defaults to sys.argv.

    Args:
        args: List of arguments to parse (defaults to sys.argv)
                Pass None to parse sys.argv automatically

    Returns:
        Parsed arguments as Namespace object with attributes matching
        the specified command and its options.

    Raises:
        SystemExit: If invalid arguments are provided (handled by argparse)

    Example:
        >>> # Parse custom arguments
        >>> args = parse_args(['export', '--output', 'test.md'])
        >>> args.output
        'test.md'
        >>> args.command
        'export'

        >>> # Parse sys.argv automatically
        >>> args = parse_args()
        >>> args.command
        'status'  # or whatever was provided
    """
    parser = create_parser()
    return parser.parse_args(args)
