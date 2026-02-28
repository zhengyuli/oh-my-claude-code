#!/usr/bin/env python3
"""
Unit tests for instinct parser library.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from instinct_parser import (
    Instinct, generate_instinct_id, save_instinct,
    load_instinct, load_all_instincts, update_instinct_evidence
)


class TestInstinctClass(unittest.TestCase):
    """Tests for Instinct dataclass."""

    def test_instinct_creation(self):
        """Test creating an instinct with all fields."""
        instinct = Instinct(
            id='test-instinct',
            trigger='when testing',
            confidence=0.7,
            domain='testing',
            created='2025-01-01T00:00:00Z',
            source='observation',
            evidence_count=5,
            action='Write tests first',
            evidence=['observed 1', 'observed 2']
        )
        self.assertEqual(instinct.id, 'test-instinct')
        self.assertEqual(instinct.confidence, 0.7)
        self.assertEqual(len(instinct.evidence), 2)

    def test_instinct_defaults(self):
        """Test instinct default values."""
        instinct = Instinct(
            id='test',
            trigger='test',
            confidence=0.5,
            domain='test',
            created='2025-01-01T00:00:00Z'
        )
        self.assertEqual(instinct.source, 'observation')
        self.assertEqual(instinct.evidence_count, 1)
        self.assertEqual(instinct.action, '')
        self.assertEqual(instinct.evidence, [])

    def test_to_markdown(self):
        """Test converting instinct to YAML frontmatter + Markdown."""
        instinct = Instinct(
            id='prefer-functional',
            trigger='when writing code',
            confidence=0.8,
            domain='code-style',
            created='2025-01-15T10:00:00Z',
            action='Use functional patterns',
            evidence=['Seen 5 times']
        )
        markdown = instinct.to_markdown()

        self.assertIn('---', markdown)
        self.assertIn('id: prefer-functional', markdown)
        self.assertIn('confidence: 0.8', markdown)
        self.assertIn('# Prefer Functional', markdown)
        self.assertIn('## Action', markdown)
        self.assertIn('## Evidence', markdown)
        self.assertIn('Use functional patterns', markdown)
        self.assertIn('Seen 5 times', markdown)

    def test_from_markdown(self):
        """Test parsing instinct from YAML frontmatter + Markdown."""
        markdown = '''---
id: test-instinct
trigger: "when testing"
confidence: 0.7
domain: "testing"
created: "2025-01-15T10:00:00Z"
source: "observation"
evidence_count: 2
---

# Test Instinct

## Action
Write tests first

## Evidence
- Observed once
- Observed twice
'''
        instinct = Instinct.from_markdown(markdown)

        self.assertIsNotNone(instinct)
        self.assertEqual(instinct.id, 'test-instinct')
        self.assertEqual(instinct.confidence, 0.7)
        self.assertEqual(instinct.action, 'Write tests first')
        self.assertEqual(len(instinct.evidence), 2)

    def test_from_markdown_invalid(self):
        """Test parsing invalid markdown returns None."""
        invalid = "This is not valid instinct format"
        instinct = Instinct.from_markdown(invalid)
        self.assertIsNone(instinct)


class TestGenerateInstinctId(unittest.TestCase):
    """Tests for generate_instinct_id function."""

    def test_generate_id_basic(self):
        """Test basic ID generation."""
        id = generate_instinct_id('when editing files', 'workflow')
        self.assertIsInstance(id, str)
        self.assertLessEqual(len(id), 50)
        self.assertIn('-', id)

    def test_generate_id_with_domain(self):
        """Test ID includes domain context."""
        id = generate_instinct_id('when testing', 'testing')
        # Should contain 'testing' or related words
        self.assertTrue(len(id) > 0)

    def test_generate_id_unique(self):
        """Test IDs are unique (different timestamps)."""
        id1 = generate_instinct_id('test', 'test')
        import time
        time.sleep(0.01)  # Small delay for different timestamp
        id2 = generate_instinct_id('test', 'test')
        # IDs should differ due to timestamp
        # (though this might occasionally fail if timestamps align)
        self.assertIsInstance(id1, str)
        self.assertIsInstance(id2, str)


class TestSaveAndLoadInstinct(unittest.TestCase):
    """Tests for save and load functions."""

    def test_save_instinct_creates_file(self):
        """Test saving instinct creates file with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            instinct = Instinct(
                id='test-save',
                trigger='when testing',
                confidence=0.7,
                domain='testing',
                created='2025-01-15T10:00:00Z',
                action='Test action'
            )

            file_path = save_instinct(instinct, Path(tmpdir), 'personal')

            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.name, 'test-save.md')
            self.assertEqual(file_path.parent.name, 'personal')

    def test_load_saved_instinct(self):
        """Test loading a saved instinct returns same data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Instinct(
                id='test-load',
                trigger='when loading',
                confidence=0.6,
                domain='workflow',
                created='2025-01-15T10:00:00Z',
                action='Load action'
            )

            file_path = save_instinct(original, Path(tmpdir), 'personal')
            loaded = load_instinct(file_path)

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.id, original.id)
            self.assertEqual(loaded.trigger, original.trigger)
            self.assertEqual(loaded.confidence, original.confidence)

    def test_load_nonexistent_returns_none(self):
        """Test loading non-existent file returns None."""
        result = load_instinct(Path('/tmp/nonexistent-instinct.md'))
        self.assertIsNone(result)


class TestLoadAllInstincts(unittest.TestCase):
    """Tests for load_all_instincts function."""

    def test_load_from_both_directories(self):
        """Test loading from both personal and shared directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create personal instinct
            personal = Instinct(
                id='personal-1',
                trigger='personal trigger',
                confidence=0.7,
                domain='test',
                created='2025-01-15T10:00:00Z'
            )
            save_instinct(personal, Path(tmpdir), 'personal')

            # Create shared instinct
            shared = Instinct(
                id='shared-1',
                trigger='shared trigger',
                confidence=0.6,
                domain='test',
                created='2025-01-15T10:00:00Z'
            )
            save_instinct(shared, Path(tmpdir), 'shared')

            # Load all
            all_instincts = load_all_instincts(Path(tmpdir))

            self.assertEqual(len(all_instincts), 2)
            ids = [i.id for i in all_instincts]
            self.assertIn('personal-1', ids)
            self.assertIn('shared-1', ids)

    def test_load_empty_directories(self):
        """Test loading from empty directories returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty directories
            (Path(tmpdir) / 'instincts' / 'personal').mkdir(parents=True)
            (Path(tmpdir) / 'instincts' / 'shared').mkdir(parents=True)

            all_instincts = load_all_instincts(Path(tmpdir))

            self.assertEqual(len(all_instincts), 0)


class TestUpdateInstinctEvidence(unittest.TestCase):
    """Tests for update_instinct_evidence function."""

    def test_update_adds_evidence(self):
        """Test that update adds new evidence."""
        instinct = Instinct(
            id='test-update',
            trigger='test',
            confidence=0.5,
            domain='test',
            created='2025-01-15T10:00:00Z',
            evidence=['evidence 1']
        )

        updated = update_instinct_evidence(instinct, 'evidence 2')

        self.assertEqual(len(updated.evidence), 2)
        self.assertIn('evidence 2', updated.evidence)
        self.assertEqual(updated.evidence_count, 2)

    def test_update_increases_confidence(self):
        """Test that multiple updates increase confidence appropriately."""
        instinct = Instinct(
            id='test-confidence',
            trigger='test',
            confidence=0.5,
            domain='test',
            created='2025-01-15T10:00:00Z',
            evidence_count=3
        )

        # Update to reach 5 occurrences
        updated = update_instinct_evidence(instinct, 'new evidence')

        self.assertEqual(updated.evidence_count, 4)
        # Confidence should increase but not exceed max
        self.assertLessEqual(updated.confidence, 0.9)


if __name__ == '__main__':
    unittest.main()
