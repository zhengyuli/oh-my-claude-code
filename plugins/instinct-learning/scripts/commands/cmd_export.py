"""Export command handler.

Exports instincts to YAML frontmatter + markdown format. Supports filtering
by domain and confidence level. Can save to file or print to stdout.
"""

from datetime import datetime
from argparse import Namespace
from pathlib import Path

from utils.file_io import load_all_instincts


def cmd_export(args: Namespace) -> int:
    """Export instincts to file or stdout.

    Filters instincts by domain and/or confidence, then exports them
    in YAML frontmatter + markdown format.
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
