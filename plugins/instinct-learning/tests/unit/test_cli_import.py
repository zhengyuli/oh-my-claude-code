# tests/unit/test_cli_import.py
import pytest
import sys
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from utils.instinct_parser import parse_instinct_file

@pytest.mark.unit
class TestImportParsing:
    """Tests for import-related parsing."""

    def test_parse_single_instinct_for_import(self):
        """Test parsing instinct for import."""
        content = '''---
id: imported-instinct
trigger: "when importing"
confidence: 0.85
domain: testing
---
# Imported Instinct
Content here.
'''
        result = parse_instinct_file(content)
        assert len(result) == 1
        assert result[0]['id'] == 'imported-instinct'
        assert result[0]['domain'] == 'testing'

    def test_parse_import_with_source_repo(self):
        """Test parsing instinct with source_repo field."""
        content = '''---
id: repo-instinct
trigger: "test"
source_repo: https://github.com/example/repo
---
Content.
'''
        result = parse_instinct_file(content)
        assert result[0]['source_repo'] == 'https://github.com/example/repo'

    @pytest.mark.parametrize("field,value", [
        ('id', 'test-id'),
        ('trigger', 'when testing'),
        ('confidence', 0.75),
        ('domain', 'workflow'),
        ('source', 'manual'),
    ])
    def test_parse_individual_fields(self, field, value):
        """Test parsing individual fields."""
        content = f'''---
id: test
{field}: {value if field != 'trigger' else '"' + value + '"'}
---
Content.
'''
        result = parse_instinct_file(content)
        if field == 'confidence':
            assert abs(result[0][field] - value) < 0.01
        else:
            assert result[0][field] == value
