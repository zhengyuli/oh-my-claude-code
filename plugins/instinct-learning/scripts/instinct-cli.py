#!/usr/bin/env python3
"""
Instinct Learning CLI

Complete command-line management tool for the instinct-learning plugin.

Usage:
    instinct-cli.py status [--domain <domain>] [--format <json|text>]
    instinct-cli.py import <file|url> [--merge]
    instinct-cli.py export [--domain <domain>] [--output <file>]
    instinct-cli.py evolve [--generate] [--dry-run]
    instinct-cli.py session [--stats]
    instinct-cli.py config [--set <key=value>]
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from pattern_detection import load_observations, detect_all_patterns
from instinct_parser import (
    Instinct, load_all_instincts, save_instinct,
    generate_instinct_id
)
from confidence import get_confidence_level, AUTO_APPROVE_THRESHOLD
from clustering import EvolutionEngine, create_clusters

# Support plugin-specific environment variable
DATA_DIR = Path(os.environ.get('INSTINCT_LEARNING_DATA_DIR', Path.home() / '.claude' / 'instinct-learning'))


def load_config() -> dict:
    """Load configuration file."""
    config_file = DATA_DIR / 'config.json'
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save configuration file."""
    config_file = DATA_DIR / 'config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def cmd_status(args):
    """Display all instincts organized by confidence level."""
    instincts = load_all_instincts(DATA_DIR)

    # Filter by domain if specified
    if args.domain:
        instincts = [i for i in instincts if i.domain == args.domain]

    if not instincts:
        print("No instincts found. Run some sessions to generate observations.")
        return

    # Group by confidence level
    high = [i for i in instincts if i.confidence >= AUTO_APPROVE_THRESHOLD]
    medium = [i for i in instincts if 0.5 <= i.confidence < AUTO_APPROVE_THRESHOLD]
    low = [i for i in instincts if i.confidence < 0.5]

    if args.format == 'json':
        output = {
            "high": [{"id": i.id, "confidence": i.confidence, "trigger": i.trigger, "domain": i.domain} for i in high],
            "medium": [{"id": i.id, "confidence": i.confidence, "trigger": i.trigger, "domain": i.domain} for i in medium],
            "low": [{"id": i.id, "confidence": i.confidence, "trigger": i.trigger, "domain": i.domain} for i in low]
        }
        print(json.dumps(output, indent=2))
    else:
        print("### High Confidence (0.7+) - Auto-Approved")
        if high:
            for i in high:
                print(f"  - [{i.confidence}] {i.id}: {i.trigger}")
        else:
            print("  (none)")

        print("\n### Medium Confidence (0.5-0.7) - Applied When Relevant")
        if medium:
            for i in medium:
                print(f"  - [{i.confidence}] {i.id}: {i.trigger}")
        else:
            print("  (none)")

        print("\n### Low Confidence (0.3-0.5) - Tentative")
        if low:
            for i in low:
                print(f"  - [{i.confidence}] {i.id}: {i.trigger}")
        else:
            print("  (none)")

        # Statistics
        print(f"\n## Stats")
        print(f"Total: {len(instincts)} | High: {len(high)} | Medium: {len(medium)} | Low: {len(low)}")

        # Check evolution readiness
        clusters = create_clusters(instincts)
        ready = [c for c in clusters if c.avg_confidence >= AUTO_APPROVE_THRESHOLD]
        if ready:
            print(f"\nEvolution ready: {', '.join(f'{c.domain} ({c.count})' for c in ready)}")


def cmd_import(args):
    """Import instincts from file or URL."""
    source = args.source
    content = ""

    if source.startswith('http://') or source.startswith('https://'):
        # URL import
        try:
            with urllib.request.urlopen(source, timeout=30) as response:
                content = response.read().decode('utf-8')
        except urllib.error.URLError as e:
            print(f"Error fetching URL: {e}")
            sys.exit(1)
    else:
        # File import
        file_path = Path(source)
        if not file_path.exists():
            print(f"File not found: {source}")
            sys.exit(1)
        with open(file_path, 'r') as f:
            content = f.read()

    # Parse instincts (expecting YAML frontmatter format)
    import re
    import yaml

    instincts = []
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*?)(?=---|\Z)'

    for match in re.finditer(pattern, content, re.DOTALL):
        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)

            # Extract action
            action_match = re.search(r'## Action\s*\n(.*?)(?:\n##|\Z)', body, re.DOTALL)
            action = action_match.group(1).strip() if action_match else ""

            instinct = Instinct(
                id=frontmatter.get('id', generate_instinct_id('imported', 'imported')),
                trigger=frontmatter.get('trigger', ''),
                confidence=float(frontmatter.get('confidence', 0.5)),
                domain=frontmatter.get('domain', 'imported'),
                created=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                source='imported',
                evidence_count=frontmatter.get('evidence_count', 1),
                action=action,
                evidence=['Imported from ' + source]
            )
            instincts.append(instinct)
        except (yaml.YAMLError, ValueError):
            continue

    if not instincts:
        print("No valid instincts found in source.")
        return

    # Save instincts
    category = 'shared'
    for instinct in instincts:
        instinct.source = 'imported'
        save_instinct(instinct, DATA_DIR, category)

    print(f"Imported {len(instincts)} instincts to {category}/")


def cmd_export(args):
    """Export instincts to file or stdout."""
    instincts = load_all_instincts(DATA_DIR)

    if args.domain:
        instincts = [i for i in instincts if i.domain == args.domain]

    if not instincts:
        print("No instincts to export.")
        return

    # Build output content
    output_parts = []
    for instinct in instincts:
        output_parts.append(instinct.to_markdown())

    output = '\n\n'.join(output_parts)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(output)
        print(f"Exported {len(instincts)} instincts to {args.output}")
    else:
        print(output)


def cmd_evolve(args):
    """Evolve instincts into capabilities."""
    instincts = load_all_instincts(DATA_DIR)

    if not instincts:
        print("No instincts to evolve. Run more sessions first.")
        return

    engine = EvolutionEngine()
    clusters = engine.analyze(instincts)

    if not clusters:
        print("No clusters found. Need more instincts in the same domain.")
        return

    print(f"Found {len(clusters)} potential clusters:\n")

    for cluster in clusters:
        print(f"Domain: {cluster.domain}")
        print(f"  Instincts: {cluster.count} (avg confidence: {cluster.avg_confidence:.2f})")
        print(f"  Type: {cluster.capability_type}")

        if args.dry_run:
            print(f"  [Dry run] Would propose: {cluster.capability_type}")
        elif args.generate:
            suggestion = engine.suggest_evolution(cluster)
            print(f"  Generated: {suggestion['name']}")
            print(f"  Description: {suggestion['description']}")
            # TODO: Actually generate capability files

        print()

    ready = engine.get_ready_clusters()
    if ready:
        print(f"Ready for evolution: {len(ready)} clusters")
    else:
        print("No clusters ready for evolution yet.")


def cmd_session(args):
    """Manage session information."""
    session_file = DATA_DIR / 'session.json'

    if args.stats:
        if session_file.exists():
            with open(session_file, 'r') as f:
                data = json.load(f)
            print(f"Total sessions: {data.get('count', 0)}")
            print(f"Last session: {data.get('last_session', 'N/A')}")
        else:
            print("No session data found.")


def cmd_config(args):
    """Manage configuration."""
    config = load_config()

    if args.set:
        key, value = args.set.split('=', 1)
        keys = key.split('.')
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Try to parse as number or boolean
        try:
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif '.' in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            pass  # Keep as string

        current[keys[-1]] = value
        save_config(config)
        print(f"Set {key} = {value}")
    else:
        print(json.dumps(config, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description='Instinct Learning CLI - Manage learned behaviors'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # status command
    p_status = subparsers.add_parser('status', help='Show all learned instincts')
    p_status.add_argument('--domain', '-d', help='Filter by domain')
    p_status.add_argument('--format', '-f', choices=['json', 'text'], default='text',
                          help='Output format')

    # import command
    p_import = subparsers.add_parser('import', help='Import instincts from file or URL')
    p_import.add_argument('source', help='File path or URL to import from')
    p_import.add_argument('--merge', '-m', action='store_true',
                          help='Merge with existing instincts')

    # export command
    p_export = subparsers.add_parser('export', help='Export instincts')
    p_export.add_argument('--domain', '-d', help='Filter by domain')
    p_export.add_argument('--output', '-o', help='Output file path')

    # evolve command
    p_evolve = subparsers.add_parser('evolve', help='Evolve instincts into capabilities')
    p_evolve.add_argument('--generate', '-g', action='store_true',
                          help='Generate capability files')
    p_evolve.add_argument('--dry-run', action='store_true',
                          help='Show what would be generated')

    # session command
    p_session = subparsers.add_parser('session', help='Session management')
    p_session.add_argument('--stats', action='store_true',
                           help='Show session statistics')

    # config command
    p_config = subparsers.add_parser('config', help='Configuration management')
    p_config.add_argument('--set', metavar='KEY=VALUE',
                          help='Set a configuration value')

    args = parser.parse_args()

    if args.command == 'status':
        cmd_status(args)
    elif args.command == 'import':
        cmd_import(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'evolve':
        cmd_evolve(args)
    elif args.command == 'session':
        cmd_session(args)
    elif args.command == 'config':
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
