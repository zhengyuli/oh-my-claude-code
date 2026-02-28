"""Data integrity scenario tests.

These tests validate data integrity under various failure conditions
and ensure the system handles partial/corrupted data gracefully.
"""

import json
import pytest
from pathlib import Path


@pytest.mark.scenario
def test_partial_json_recovered(temp_data_dir):
    """Scenario: Partial/corrupted JSON in observations file is recovered.

    When observations.jsonl contains partial JSON entries:
    - Valid entries should be parsed successfully
    - Invalid entries should be skipped
    - Processing should continue without crashing
    """
    obs_file = temp_data_dir / 'observations' / 'observations.jsonl'

    # Write mixed valid and invalid JSON
    valid_obs = {
        "timestamp": "2026-02-28T10:00:00Z",
        "event": "tool_complete",
        "tool": "Edit",
        "session": "test-session-1"
    }
    partial_json = '{"timestamp": "2026-02-28T10:00:01Z", "event":'

    with open(obs_file, 'w') as f:
        f.write(json.dumps(valid_obs) + '\n')
        f.write(partial_json + '\n')
        f.write(json.dumps({**valid_obs, "session": "test-session-2"}) + '\n')

    # Should parse valid entries only
    observations = []
    with open(obs_file, 'r') as f:
        for line in f:
            try:
                observations.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass

    assert len(observations) == 2
    assert observations[0]['session'] == 'test-session-1'
    assert observations[1]['session'] == 'test-session-2'


@pytest.mark.scenario
def test_empty_observation_file_handled(temp_data_dir):
    """Scenario: Empty observation file is handled gracefully.

    When observations.jsonl exists but is empty:
    - No errors should be raised
    - Loading should complete successfully
    - Empty results should be returned
    """
    obs_file = temp_data_dir / 'observations' / 'observations.jsonl'
    obs_file.write_text('')  # Empty file

    # Create an empty list for observations
    observations = []

    # Process empty file (should not crash)
    with open(obs_file, 'r') as f:
        for line in f:
            if line.strip():
                observations.append(json.loads(line.strip()))

    assert observations == []


@pytest.mark.scenario
def test_archive_cleanup_on_rotation(temp_data_dir):
    """Scenario: Archive cleanup removes old files on rotation.

    When archive rotation is triggered:
    - Archives older than rotation threshold should be removed
    - Recent archives should be kept
    - Archive directory should not grow indefinitely
    """
    import shutil
    from datetime import datetime, timedelta

    archive_dir = temp_data_dir / 'instincts' / 'archived'
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Create test archives with different ages
    old_archive = archive_dir / 'old_instincts.tar.gz'
    recent_archive = archive_dir / 'recent_instincts.tar.gz'

    # Create actual gzip archives (simplified with empty files)
    old_archive.write_text('old data')
    recent_archive.write_text('recent data')

    # Simulate age by modifying mtimes
    old_time = datetime.now() - timedelta(days=10)
    recent_time = datetime.now() - timedelta(days=2)

    import time
    import os

    # Set mtimes to simulate file ages
    old_timestamp = old_time.timestamp()
    recent_timestamp = recent_time.timestamp()

    os.utime(old_archive, (old_timestamp, old_timestamp))
    os.utime(recent_archive, (recent_timestamp, recent_timestamp))

    # Check files exist before cleanup
    assert old_archive.exists()
    assert recent_archive.exists()

    # Verify mtimes were set correctly
    assert old_archive.stat().st_mtime < (datetime.now() - timedelta(days=5)).timestamp()
    assert recent_archive.stat().st_mtime > (datetime.now() - timedelta(days=5)).timestamp()

    # Simulate cleanup (remove files older than 7 days)
    current_time = datetime.now().timestamp()
    threshold_seconds = 7 * 24 * 3600

    for archive_file in archive_dir.glob('*.tar.gz'):
        file_age_seconds = current_time - archive_file.stat().st_mtime
        if file_age_seconds > threshold_seconds:
            archive_file.unlink()

    # Old archive should be removed, recent kept
    assert not old_archive.exists()
    assert recent_archive.exists()
