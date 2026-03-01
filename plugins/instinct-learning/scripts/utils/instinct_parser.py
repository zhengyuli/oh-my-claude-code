"""
Safe YAML frontmatter parser for instinct files.

SECURITY: Uses yaml.safe_load() to prevent code injection attacks.
"""

import re
import yaml
from typing import List, Dict, Any

# Allowed keys (prevent injection via unknown keys)
ALLOWED_KEYS = {
    'id', 'trigger', 'confidence', 'domain', 'source',
    'created', 'last_observed', 'evidence_count', 'source_repo'
}

MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0


def validate_confidence(value: Any) -> float:
    """Validate confidence is within valid range."""
    try:
        conf = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Confidence must be a number") from e

    if not (MIN_CONFIDENCE <= conf <= MAX_CONFIDENCE):
        raise ValueError(f"Confidence must be {MIN_CONFIDENCE}-{MAX_CONFIDENCE}, got {conf}")
    return conf


def sanitize_string(value: str) -> str:
    """Remove control characters that could cause issues."""
    if not isinstance(value, str):
        return str(value)
    # Remove null bytes and control characters (except newline, tab)
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', value)


def parse_instinct_file(content: str) -> List[Dict[str, Any]]:
    """Parse instinct file using safe YAML parsing.

    SECURITY: Uses yaml.safe_load() to prevent arbitrary code execution.
    """
    instincts = []
    current = {}
    in_frontmatter = False
    content_lines = []
    frontmatter_lines = []

    for line in content.split('\n'):
        if line.strip() == '---':
            if in_frontmatter:
                # End of frontmatter - parse safely
                try:
                    frontmatter_str = '\n'.join(frontmatter_lines)
                    parsed = yaml.safe_load(frontmatter_str)

                    if isinstance(parsed, dict):
                        # Only keep allowed keys
                        parsed = {k: v for k, v in parsed.items() if k in ALLOWED_KEYS}

                        # Validate confidence if present
                        if 'confidence' in parsed:
                            parsed['confidence'] = validate_confidence(parsed['confidence'])

                        # Sanitize string values
                        for key, value in parsed.items():
                            if isinstance(value, str):
                                parsed[key] = sanitize_string(value)

                        current.update(parsed)
                except (yaml.YAMLError, ValueError):
                    # Skip malformed entries
                    pass

                in_frontmatter = False
                frontmatter_lines = []
            else:
                # Start of frontmatter - save previous instinct
                if current:
                    current['content'] = '\n'.join(content_lines).strip()
                    instincts.append(current)
                current = {}
                content_lines = []
                in_frontmatter = True
        elif in_frontmatter:
            frontmatter_lines.append(line)
        else:
            content_lines.append(line)

    # Don't forget the last instinct
    if current:
        current['content'] = '\n'.join(content_lines).strip()
        instincts.append(current)

    # Filter out instincts without valid ID
    return [i for i in instincts if i.get('id')]
