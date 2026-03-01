"""
Export command handler.

This module handles exporting instincts to various formats, supporting filtering
by domain and confidence level. Exported instincts can be saved to a file or
printed to stdout for sharing with others.

Supported Output Formats:
- YAML frontmatter + markdown (default)
- Compatible with import command for round-trip data transfer

Filtering Options:
- domain: Filter by instinct domain (testing, workflow, etc.)
- min_confidence: Only export instincts above threshold

Usage Examples:
    # Export all instincts to file
    $ python3 instinct_cli.py export --output my-instincts.md

    # Export only testing domain
    $ python3 instinct_cli.py export --domain testing --output testing.md

    # Export high-confidence instincts to stdout
    $ python3 instinct_cli.py export --min-confidence 0.8

Output Format:
    Each exported instinct includes:
    - YAML frontmatter with all metadata (id, trigger, confidence, domain, etc.)
    - Original markdown content section
    - Header with export date and total count
"""

from datetime import datetime
from argparse import Namespace
from pathlib import Path

from utils.file_io import load_all_instincts


def cmd_export(args: Namespace) -> int:
    """Export instincts to file.

    This function filters instincts based on domain and/or confidence level,
    then exports them in YAML frontmatter + markdown format. The output can
    be directed to a file or printed to stdout.

    Args:
        args: argparse.Namespace with attributes:
            - output: Output file path (optional, prints to stdout if not provided)
            - domain: Filter by domain (optional)
            - min_confidence: Minimum confidence threshold (optional)

    Returns:
        0 on success, 1 if no instincts match criteria.

    Raises:
        IOError: If output file cannot be written

    Example:
        >>> cmd_export(Namespace(output='test.md', domain=None, min_confidence=0.7))
        # Exports instincts with confidence >= 0.7 to test.md
    """
    instincts = load_all_instincts()

    if not instincts:
        print("No instincts to export.")
        return 1

    if args.domain:
        instincts = [i for i in instincts if i.get('domain') == args.domain]

    if args.min_confidence:
        instincts = [i for i in instincts if i.get('confidence', 0.5) >= args.min_confidence]

    if not instincts:
        print("No instincts match the criteria.")
        return 1

    iso_date = datetime.now().isoformat()
    output = (
        f"# Instincts export\n"
        f"# Date: {iso_date}\n"
        f"# Total: {len(instincts)}\n\n"
    )

    for inst in instincts:
        output += "---\n"
        for key in ['id', 'trigger', 'confidence', 'domain', 'source', 'source_repo']:
            if inst.get(key):
                value = inst[key]
                if key == 'trigger':
                    output += f'{key}: "{value}"\n'
                else:
                    output += f"{key}: {value}\n"
        output += "---\n\n"
        output += inst.get('content', '') + "\n\n"

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Exported {len(instincts)} instincts to {args.output}")
    else:
        print(output)

    return 0
