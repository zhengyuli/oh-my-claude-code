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
    Handles multiple instincts per file with YAML frontmatter + markdown content.

    Args:
        content: File content with YAML frontmatter blocks separated by ---.

    Returns:
        List of validated instinct dictionaries with metadata and content.

    Examples:
        >>> content = "---\\nid: test\\n---\\nContent here"
        >>> parse_instinct_file(content)
        [{'id': 'test', 'content': 'Content here'}]
    """
    instincts = []

    # Split on --- delimiters
    # Note: Keep empty parts to handle instincts with empty content
    parts = [p for p in re.split(r'^---$', content, flags=re.MULTILINE)]

    # Skip first part if empty (content before first ---)
    if parts and parts[0].strip() == '':
        parts = parts[1:]

    # Process in pairs: (frontmatter, content)
    # Last item without a pair gets empty content
    for i in range(0, len(parts), 2):
        frontmatter_str = parts[i].strip() if i < len(parts) else ''
        content_str = parts[i + 1].strip() if i + 1 < len(parts) else ''

        try:
            parsed = yaml.safe_load(frontmatter_str)
            if not isinstance(parsed, dict):
                continue

            # Security: Only keep allowed keys
            parsed = {k: v for k, v in parsed.items() if k in ALLOWED_KEYS}

            # Validate confidence if present
            if 'confidence' in parsed:
                parsed['confidence'] = validate_confidence(parsed['confidence'])

            # Sanitize string values
            for key, value in parsed.items():
                if isinstance(value, str):
                    parsed[key] = sanitize_string(value)

            parsed['content'] = content_str
            instincts.append(parsed)

        except (yaml.YAMLError, ValueError):
            # Skip malformed entries
            continue

    # Filter out instincts without valid ID
    return [i for i in instincts if i.get('id')]
