"""
YAML frontmatter parser for instinct files.

This module provides functions for parsing instinct files in YAML
frontmatter + markdown format.
"""

from typing import List, Dict, Any


def parse_instinct_file(content: str) -> List[Dict[str, Any]]:
    """Parse instinct file in YAML frontmatter + markdown format.

    The instinct file format consists of one or more instincts separated by
    '---' delimiters. Each instinct has YAML frontmatter with metadata
    followed by markdown content.

    Format example:
        ---
        id: test-instinct
        trigger: "when testing code"
        confidence: 0.85
        domain: testing
        ---
        # Test Instinct

        ## Action
        Run tests.

    Args:
        content: Raw file content as string

    Returns:
        List of instinct dictionaries with parsed frontmatter fields.
        Only instincts with valid 'id' field are included.

    Raises:
        Does not raise. Malformed frontmatter is silently skipped.

    Example:
        >>> content = '''---\\nid: test\\ntrigger: "x"\\n---\\nContent'''
        >>> parse_instinct_file(content)
        [{'id': 'test', 'trigger': 'x', 'content': 'Content'}]
    """
    instincts = []
    current = {}
    in_frontmatter = False
    content_lines = []

    for line in content.split('\n'):
        if line.strip() == '---':
            # Toggle frontmatter state
            if in_frontmatter:
                in_frontmatter = False
            else:
                in_frontmatter = True
                # Save previous instinct if exists
                if current:
                    current['content'] = '\n'.join(content_lines).strip()
                    instincts.append(current)
                current = {}
                content_lines = []
        elif in_frontmatter:
            # Parse key-value pairs from frontmatter
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Confidence must be a float
                if key == 'confidence':
                    current[key] = float(value)
                else:
                    current[key] = value
        else:
            # Collect markdown content
            content_lines.append(line)

    # Don't forget the last instinct
    if current:
        current['content'] = '\n'.join(content_lines).strip()
        instincts.append(current)

    # Filter out instincts without valid ID
    return [i for i in instincts if i.get('id')]
