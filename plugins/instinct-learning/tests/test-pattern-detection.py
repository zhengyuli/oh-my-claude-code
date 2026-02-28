#!/usr/bin/env python3
"""
Unit tests for pattern detection library.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from pattern_detection import (
    load_observations,
    extract_tool_sequences,
    detect_repeated_sequences,
    detect_error_fix_patterns,
    detect_tool_preferences,
    detect_all_patterns,
    group_patterns_by_domain,
    Pattern
)


class TestLoadObservations(unittest.TestCase):
    """Tests for load_observations function."""

    def test_load_empty_file(self):
        """Test loading from non-existent file."""
        obs_file = Path('/tmp/nonexistent_test_observations.jsonl')
        result = load_observations(obs_file)
        self.assertEqual(result, [])

    def test_load_valid_observations(self):
        """Test loading valid observations with proper format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            obs_file = Path(tmpdir) / 'observations.jsonl'
            observations = [
                {"timestamp": "2025-01-01T00:00:00Z", "type": "pre_tool", "tool": "Edit", "session": "s1"},
                {"timestamp": "2025-01-01T00:01:00Z", "type": "post_tool", "tool": "Edit", "session": "s1", "exit_code": "0"}
            ]
            with open(obs_file, 'w') as f:
                for obs in observations:
                    f.write(json.dumps(obs) + '\n')

            result = load_observations(obs_file)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['tool'], 'Edit')
            self.assertEqual(result[0]['type'], 'pre_tool')

    def test_load_skips_invalid_json(self):
        """Test that invalid JSON lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            obs_file = Path(tmpdir) / 'observations.jsonl'
            with open(obs_file, 'w') as f:
                f.write('{"timestamp":"2025-01-01T00:00:00Z","type":"pre_tool","tool":"Edit","session":"s1"}\n')
                f.write('this is not valid json at all\n')
                f.write('{"timestamp":"2025-01-01T00:01:00Z","type":"post_tool","tool":"Read","session":"s1"}\n')

            result = load_observations(obs_file)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['tool'], 'Edit')
            self.assertEqual(result[1]['tool'], 'Read')


class TestSequenceDetection(unittest.TestCase):
    """Tests for sequence detection."""

    def test_extract_sequences_basic(self):
        """Test basic sequence extraction."""
        observations = [
            {"timestamp": "2025-01-01T00:00:00Z", "type": "pre_tool", "tool": "Read", "session": "s1"},
            {"timestamp": "2025-01-01T00:01:00Z", "type": "pre_tool", "tool": "Edit", "session": "s1"},
            {"timestamp": "2025-01-01T00:02:00Z", "type": "pre_tool", "tool": "Write", "session": "s1"},
            {"timestamp": "2025-01-01T00:03:00Z", "type": "pre_tool", "tool": "Bash", "session": "s1"},
        ]
        sequences = extract_tool_sequences(observations, min_length=2)
        self.assertIn(('Read', 'Edit'), sequences)
        self.assertIn(('Edit', 'Write'), sequences)

    def test_detect_repeated_sequences(self):
        """Test detection of repeated sequences."""
        observations = []
        # Create 3 sessions with same sequence - matching real format
        for session_num in range(3):
            for i, tool in enumerate(['Read', 'Edit', 'Write']):
                observations.append({
                    "timestamp": f"2025-01-0{session_num+1}T00:0{i}:00Z",
                    "type": "pre_tool",
                    "tool": tool,
                    "session": f"s{session_num}"
                })

        patterns = detect_repeated_sequences(observations, min_occurrences=3)
        self.assertTrue(len(patterns) > 0)
        # Should detect the Read→Edit→Write sequence
        found = any('Read' in str(p.pattern) and 'Write' in str(p.pattern) for p in patterns)
        self.assertTrue(found, "Should detect Read→Edit→Write sequence")


class TestErrorFixDetection(unittest.TestCase):
    """Tests for error-fix pattern detection."""

    def test_detect_error_fix(self):
        """Test detection of error followed by fix."""
        observations = [
            {"timestamp": "2025-01-01T00:00:00Z", "type": "post_tool", "tool": "Bash", "session": "s1", "exit_code": "1"},
            {"timestamp": "2025-01-01T00:01:00Z", "type": "post_tool", "tool": "Read", "session": "s1", "exit_code": "0"},
            {"timestamp": "2025-01-01T00:02:00Z", "type": "post_tool", "tool": "Edit", "session": "s1", "exit_code": "0"},
            # Second occurrence
            {"timestamp": "2025-01-01T00:10:00Z", "type": "post_tool", "tool": "Bash", "session": "s1", "exit_code": "1"},
            {"timestamp": "2025-01-01T00:11:00Z", "type": "post_tool", "tool": "Read", "session": "s1", "exit_code": "0"},
        ]
        patterns = detect_error_fix_patterns(observations)
        # Should detect Bash→Read error-fix pattern (2 occurrences)
        self.assertTrue(len(patterns) > 0, "Should detect at least one error-fix pattern")


class TestToolPreferences(unittest.TestCase):
    """Tests for tool preference detection."""

    def test_detect_tool_preference(self):
        """Test detection of tool preferences."""
        observations = []
        # Create observations with 50% Edit usage
        for i in range(10):
            observations.append({
                "timestamp": f"2025-01-01T00:{i:02d}:00Z",
                "type": "pre_tool",
                "tool": "Edit" if i < 5 else "Read",
                "session": "s1"
            })

        patterns = detect_tool_preferences(observations)
        # Should detect preferences (Edit at 50%, Read at 50% - both >20% threshold)
        self.assertTrue(len(patterns) > 0, "Should detect tool preferences")


class TestPatternGrouping(unittest.TestCase):
    """Tests for pattern grouping."""

    def test_group_by_domain(self):
        """Test grouping patterns by domain."""
        patterns = [
            Pattern('seq1', ['Read', 'Edit'], 0.7, 3, 'testing', []),
            Pattern('seq2', ['Bash'], 0.6, 2, 'git', []),
            Pattern('seq3', ['Write'], 0.8, 4, 'testing', []),
        ]
        grouped = group_patterns_by_domain(patterns)

        self.assertIn('testing', grouped)
        self.assertIn('git', grouped)
        self.assertEqual(len(grouped['testing']), 2)
        self.assertEqual(len(grouped['git']), 1)


class TestDetectAllPatterns(unittest.TestCase):
    """Tests for comprehensive pattern detection."""

    def test_detect_all(self):
        """Test running all detection algorithms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            obs_file = Path(tmpdir) / 'observations.jsonl'
            # Create realistic observation data
            observations = [
                {"timestamp": f"2025-01-01T00:{i:02d}:00Z", "type": "pre_tool", "tool": "Edit", "session": "s1"}
                for i in range(10)
            ]
            with open(obs_file, 'w') as f:
                for obs in observations:
                    f.write(json.dumps(obs) + '\n')

            loaded = load_observations(obs_file)
            patterns = detect_all_patterns(loaded)

            # Should detect tool preference for Edit (100% usage)
            self.assertTrue(len(patterns) > 0, "Should detect at least one pattern")
            # Verify at least one pattern has Edit tool
            found_edit = any('Edit' in str(p.pattern) for p in patterns)
            self.assertTrue(found_edit, "Should detect Edit as preferred tool")


if __name__ == '__main__':
    unittest.main()
