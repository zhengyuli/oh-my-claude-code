"""
Command handlers for Instinct CLI.

This package provides all command implementations for the instinct-learning
CLI. Each command is implemented as a separate module for better maintainability.

Available Commands:
    status: Display all learned instincts with confidence scores
    import: Import instincts from file or URL
    export: Export instincts to file or stdout
    prune: Enforce max instincts limit by archiving low-confidence ones
    decay: Show effective confidence after time-based decay

Command Module Structure:
    Each command module exports a single function: cmd_<command>(args: Namespace) -> int
    Return value: 0 on success, 1 on error

Architecture:
    Commands use utility modules (utils/) for file I/O, confidence calculation,
    and YAML parsing. Commands orchestrate these utilities to implement their
    specific functionality.
"""

from .cmd_status import cmd_status
from .cmd_import import cmd_import
from .cmd_export import cmd_export
from .cmd_prune import cmd_prune, enforce_max_instincts
from .cmd_decay import cmd_decay

__all__ = [
    'cmd_status',
    'cmd_import',
    'cmd_export',
    'cmd_prune',
    'enforce_max_instincts',
    'cmd_decay',
]
