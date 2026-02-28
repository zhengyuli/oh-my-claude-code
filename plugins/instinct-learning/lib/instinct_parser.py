#!/usr/bin/env python3
"""
Instinct Parser Library

Parses and generates instinct files in YAML frontmatter + Markdown format.
"""

import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None
    import warnings
    warnings.warn("PyYAML not installed. Install with: pip install pyyaml", ImportWarning)


@dataclass
class Instinct:
    """Represents a learned instinct."""
    id: str
    trigger: str
    confidence: float
    domain: str
    created: str
    source: str = "observation"
    evidence_count: int = 1
    action: str = ""
    evidence: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert instinct to YAML frontmatter + Markdown format."""
        if yaml is None:
            raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")

        frontmatter = {
            'id': self.id,
            'trigger': self.trigger,
            'confidence': self.confidence,
            'domain': self.domain,
            'created': self.created,
            'source': self.source,
            'evidence_count': self.evidence_count
        }

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Format title from id
        title = self.id.replace('-', ' ').title()

        # Build evidence section
        evidence_str = '\n'.join(f"- {e}" for e in self.evidence) if self.evidence else "- No evidence recorded"

        return f"""---
{yaml_str}---

# {title}

## Action
{self.action or f"When {self.trigger}, apply this learned behavior."}

## Evidence
{evidence_str}
"""

    @classmethod
    def from_markdown(cls, content: str) -> Optional['Instinct']:
        """Parse instinct from YAML frontmatter + Markdown content."""
        if yaml is None:
            raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")

        # Extract frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)

            # Extract action from body
            action_match = re.search(r'## Action\s*\n(.*?)(?:\n##|\Z)', body, re.DOTALL)
            action = action_match.group(1).strip() if action_match else ""

            # Extract evidence from body
            evidence = []
            evidence_match = re.search(r'## Evidence\s*\n(.*?)(?:\n##|\Z)', body, re.DOTALL)
            if evidence_match:
                evidence_text = evidence_match.group(1).strip()
                evidence = [
                    line.strip().lstrip('- ').strip()
                    for line in evidence_text.split('\n')
                    if line.strip().startswith('-')
                ]

            return cls(
                id=frontmatter.get('id', ''),
                trigger=frontmatter.get('trigger', ''),
                confidence=float(frontmatter.get('confidence', 0.3)),
                domain=frontmatter.get('domain', 'workflow'),
                created=frontmatter.get('created', datetime.utcnow().isoformat()),
                source=frontmatter.get('source', 'observation'),
                evidence_count=int(frontmatter.get('evidence_count', 1)),
                action=action,
                evidence=evidence
            )
        except (yaml.YAMLError, ValueError, TypeError):
            return None


def generate_instinct_id(trigger: str, domain: str) -> str:
    """Generate a unique instinct ID from trigger and domain."""
    # Extract key words from trigger
    words = re.findall(r'\b[a-zA-Z]{3,}\b', trigger.lower())
    key_words = [w for w in words if w not in ['when', 'the', 'for', 'and', 'with']]

    if key_words:
        base_id = '-'.join(key_words[:3])
    else:
        base_id = domain

    # Add timestamp suffix for uniqueness
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')

    return f"{base_id}-{timestamp}"[:50]


def save_instinct(instinct: Instinct, base_path: Path, category: str = 'personal') -> Path:
    """Save instinct to file."""
    category_path = base_path / 'instincts' / category
    category_path.mkdir(parents=True, exist_ok=True)

    filename = f"{instinct.id}.md"
    file_path = category_path / filename

    content = instinct.to_markdown()
    with open(file_path, 'w') as f:
        f.write(content)

    return file_path


def load_instinct(file_path: Path) -> Optional[Instinct]:
    """Load instinct from file."""
    if not file_path.exists():
        return None

    with open(file_path, 'r') as f:
        content = f.read()

    return Instinct.from_markdown(content)


def load_all_instincts(base_path: Path) -> list[Instinct]:
    """Load all instincts from personal and shared directories."""
    instincts = []

    for category in ['personal', 'shared']:
        category_path = base_path / 'instincts' / category
        if category_path.exists():
            for file_path in category_path.glob('*.md'):
                instinct = load_instinct(file_path)
                if instinct:
                    instincts.append(instinct)

    return instincts


def update_instinct_evidence(instinct: Instinct, new_evidence: str) -> Instinct:
    """Update instinct with new evidence and increment count."""
    instinct.evidence.append(new_evidence)
    instinct.evidence_count += 1

    # Adjust confidence based on evidence count
    if instinct.evidence_count >= 10:
        instinct.confidence = min(0.9, instinct.confidence + 0.1)
    elif instinct.evidence_count >= 5:
        instinct.confidence = min(0.8, instinct.confidence + 0.05)

    return instinct


if __name__ == '__main__':
    # Test instinct creation and parsing
    test_instinct = Instinct(
        id='prefer-functional-style',
        trigger='when writing new functions',
        confidence=0.7,
        domain='code-style',
        created=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        action='Use functional patterns over classes when appropriate.',
        evidence=[
            'Observed in 5 different sessions',
            'User consistently uses map/filter/reduce'
        ]
    )

    markdown = test_instinct.to_markdown()
    print("Generated Markdown:")
    print(markdown)
    print()

    parsed = Instinct.from_markdown(markdown)
    if parsed:
        print(f"Parsed successfully: {parsed.id} (confidence: {parsed.confidence})")
    else:
        print("Failed to parse")
