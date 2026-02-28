# Comprehensive Test Coverage Design for instinct-learning Plugin

**Date**: 2026-02-28
**Author**: Claude Code
**Status**: Approved
**Goal**: Production readiness with comprehensive coverage

## Overview

A comprehensive testing suite for the instinct-learning plugin using pytest, combining module-specific unit tests with scenario-based integration tests. The design covers all production concerns: data integrity, performance, and reliability.

**Target**: ~230 test cases covering unit, integration, and scenario testing.

## Test Architecture

```
tests/
├── fixtures.py              # 共享测试数据（增强现有）
├── conftest.py              # pytest 共享 fixtures（新建）
├── run_all.sh               # 统一测试运行脚本（更新现有）
├── unit/                    # 单元测试（新建）
│   ├── test_cli_parser.py           # CLI 解析器
│   ├── test_cli_confidence.py       # 置信度计算
│   ├── test_cli_evolution.py        # 进化逻辑
│   ├── test_cli_import.py           # 导入功能
│   ├── test_cli_export.py           # 导出功能
│   ├── test_cli_prune.py            # 清理功能
│   └── test_rotation.py             # 文件轮转逻辑
├── integration/             # 集成测试（新建）
│   ├── test_cli_integration.py      # CLI 命令集成
│   ├── test_hooks_integration.py    # Hooks 系统集成
│   └── test_observer_integration.py # Observer 集成
└── scenarios/               # 场景测试（新建）
    ├── test_data_integrity.py       # 数据完整性
    ├── test_performance.py          # 性能测试
    ├── test_error_handling.py       # 错误处理
    └── test_edge_cases.py           # 边界情况
```

**Note**: 现有测试文件 `test_instinct_cli.py`、`test_hooks.py`、`test_observe_sh.py`、`test_integration.py` 将被合并/重构到新结构中。

## Pytest Configuration

### `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    scenario: Scenario tests
    slow: Slow-running tests
```

### `tests/conftest.py` - Shared Fixtures

```python
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_data_dir():
    """临时数据目录，每个测试独立"""
    temp_dir = Path(tempfile.mkdtemp())
    data_dir = temp_dir / '.claude' / 'instinct-learning'
    data_dir.mkdir(parents=True)
    (data_dir / 'instincts' / 'personal').mkdir(parents=True)
    (data_dir / 'instincts' / 'inherited').mkdir(parents=True)
    (data_dir / 'instincts' / 'archived').mkdir(parents=True)
    (data_dir / 'observations').mkdir(parents=True)
    yield data_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_observations():
    """示例观察数据"""
    return [...]

@pytest.fixture
def sample_instincts():
    """示例本能数据"""
    return [...]

@pytest.fixture
def large_dataset():
    """大型数据集用于性能测试"""
    return [...]
```

## Unit Tests (~150 test cases)

### `test_cli_parser.py` - Instinct File Parsing

- `test_parse_single_instinct` - 正常单个本能
- `test_parse_multiple_instincts` - 多个本能
- `test_parse_empty_frontmatter` - 空 frontmatter
- `test_parse_missing_id` - 缺少 ID
- `test_parse_missing_confidence` - 缺少置信度（使用默认值）
- `test_parse_quoted_values` - 不同引号风格
- `test_parse_special_chars` - 特殊字符
- `test_parse_unicode_content` - Unicode 内容
- `test_parse_very_long_content` - 超长内容
- `test_parse_malformed_yaml` - 格式错误的 YAML
- `test_parse_with_action_section` - 带 Action 部分
- `test_parse_with_evidence_section` - 带 Evidence 部分

### `test_cli_confidence.py` - Confidence Calculation

- `test_confidence_no_decay` - 无衰减
- `test_confidence_one_week_decay` - 一周衰减
- `test_confidence_multiple_weeks_decay` - 多周衰减
- `test_confidence_floor_at_0_3` - 最低值 0.3
- `test_confidence_missing_last_observed` - 缺少 last_observed
- `test_confidence_invalid_timestamp` - 无效时间戳
- `test_confidence_custom_decay_rate` - 自定义衰减率
- `test_confidence_zero_decay_rate` - 零衰减率
- `test_confidence_timezone_handling` - 时区处理
- `test_confidence_edge_case_dates` - 边界日期

### `test_cli_evolution.py` - Evolution Logic

- `test_evolve_insufficient_instincts` - 本能不足
- `test_evolve_skill_detection` - 技能检测
- `test_evolve_command_detection` - 命令检测
- `test_evolve_agent_detection` - 代理检测
- `test_evolve_clustering_by_domain` - 按领域聚类
- `test_evolve_trigger_similarity` - 触发器相似度
- `test_evolve_generate_skills` - 生成技能
- `test_evolve_generate_commands` - 生成命令
- `test_evolve_generate_agents` - 生成代理
- `test_evolve_with_low_confidence_filter` - 低置信度过滤

### `test_cli_import.py` - Import Functionality

- `test_import_from_file` - 从文件导入
- `test_import_from_url` - 从 URL 导入
- `test_import_dry_run` - 干运行
- `test_import_with_force` - 强制导入
- `test_import_with_min_confidence` - 最小置信度过滤
- `test_import_duplicate_handling` - 重复处理
- `test_import_update_existing` - 更新已存在
- `test_import_malformed_source` - 格式错误源
- `test_import_file_not_found` - 文件不存在
- `test_import_url_error_handling` - URL 错误处理

### `test_cli_export.py` - Export Functionality

- `test_export_all_instincts` - 导出所有本能
- `test_export_by_domain` - 按领域导出
- `test_export_with_min_confidence` - 最小置信度过滤
- `test_export_to_file` - 导出到文件
- `test_export_to_stdout` - 导出到标准输出
- `test_export_empty_instincts` - 空本能导出
- `test_export_format_validation` - 格式验证

### `test_cli_prune.py` - Prune Functionality

- `test_prune_within_limit` - 在限制内
- `test_prune_exceeds_limit` - 超过限制
- `test_prune_dry_run` - 干运行
- `test_prune_custom_limit` - 自定义限制
- `test_prune_archives_low_confidence` - 归档低置信度
- `test_prune_with_decay_calculation` - 带衰减计算
- `test_prune_file_movement` - 文件移动
- `test_prune_name_conflict_handling` - 名称冲突处理

### `test_rotation.py` - File Rotation Logic

- `test_rotation_at_threshold` - 达到阈值时轮转
- `test_rotation_multiple_files` - 多文件轮转
- `test_rotation_max_archives_limit` - 最大归档限制
- `test_rotation_oldest_deleted` - 删除最旧归档
- `test_rotation_numbered_sequence` - 编号序列
- `test_rotation_preserves_data` - 保持数据

## Integration Tests (~50 test cases)

### `test_cli_integration.py` - CLI Command Integration

- `test_full_workflow_import_status_export` - 完整工作流
- `test_import_with_update_existing` - 导入更新
- `test_evolve_with_generate` - 进化生成
- `test_prune_enforces_limit` - 清理强制限制
- `test_decay_shows_effective` - 衰减显示有效值
- `test_multiple_imports_accumulate` - 多次导入累积
- `test_export_after_import` - 导入后导出
- `test_status_shows_all_domains` - 状态显示所有领域

### `test_hooks_integration.py` - Hooks System Integration

- `test_pre_post_hook_creates_complete_pair` - 完整观察对
- `test_multiple_sessions_tracked_correctly` - 多会话跟踪
- `test_rotation_preserves_data_integrity` - 轮转保持数据
- `test_disabled_flag_prevents_all_writes` - 禁用标志阻止写入
- `test_hook_creates_directory_if_missing` - 创建缺失目录
- `test_concurrent_hooks_dont_corrupt` - 并发不损坏数据
- `test_hook_execution_time_under_limit` - 执行时间限制
- `test_all_observed_tools_captured` - 所有工具被捕获

### `test_observer_integration.py` - Observer Integration

- `test_observer_reads_archived_files_only` - 仅读取归档
- `test_observer_detects_repeated_patterns` - 检测重复模式
- `test_observer_creates_instinct_files` - 创建本能文件
- `test_observer_updates_existing_instincts` - 更新已存在本能
- `test_observer_enforces_max_limit` - 强制最大限制
- `test_observer_cleanup_archives` - 清理归档
- `test_observer_with_insufficient_data` - 数据不足处理

## Scenario Tests (~30 test cases)

### `test_data_integrity.py` - Data Integrity Scenarios

- `test_concurrent_write_safety` - 并发写入安全性
- `test_file_rotation_during_write` - 写入时轮转
- `test_partial_json_recovery` - 不完整 JSON 恢复
- `test_archive_cleanup_preserves_data` - 归档清理保持数据
- `test_crash_during_write_recovery` - 写入崩溃恢复
- `test_disk_full_handling` - 磁盘满处理

### `test_performance.py` - Performance Scenarios

- `test_large_observation_file_parsing` - 大型观察文件解析
- `test_thousands_of_instincts_loading` - 加载数千本能
- `test_hook_execution_time_under_limit` - Hook 执行时间
- `test_cli_status_with_many_instincts` - 大量本能状态
- `test_evolve_with_many_instincts` - 大量本能进化
- `test_import_large_file` - 大文件导入

### `test_error_handling.py` - Error Handling Scenarios

- `test_malformed_observations_skipped_gracefully` - 优雅跳过错误观察
- `test_disk_space_exhaustion_handled` - 磁盘空间耗尽
- `test_permission_denied_scenarios` - 权限被拒绝
- `test_network_timeout_on_url_import` - URL 导入超时
- `test_invalid_schema_in_config` - 无效配置模式
- `test_corrupted_instinct_files` - 损坏本能文件

### `test_edge_cases.py` - Edge Cases

- `test_empty_observations_file` - 空观察文件
- `test_single_instinct_evolution` - 单个本能进化
- `test_confidence_at_boundaries` - 置信度边界值
- `test_unicode_in_all_fields` - 所有字段 Unicode
- `test_very_long_trigger_strings` - 超长触发器字符串
- `test_special_characters_in_paths` - 路径特殊字符

## Test Execution

### `tests/run_all.sh` - Updated Test Runner

```bash
#!/bin/bash
# 支持运行不同类别的测试
./tests/run_all.sh              # 所有测试
./tests/run_all.sh --unit       # 仅单元测试
./tests/run_all.sh --integration # 仅集成测试
./tests/run_all.sh --scenario   # 仅场景测试
./tests/run_all.sh --coverage   # 带覆盖率报告
```

### Coverage Targets

- **Line Coverage**: 80%+
- **Branch Coverage**: 70%+
- **Function Coverage**: 90%+

## Implementation Notes

1. **使用 pytest.mark** 标记测试类别以便选择性运行
2. **参数化测试** 用于测试多种输入变体
3. **fixtures** 用于共享测试数据和设置
4. **临时目录** 确保测试隔离
5. **清理操作** 在 tearDown 中进行

## Dependencies

```bash
pip install pytest pytest-cov pytest-mock
```

## Success Criteria

- 所有测试通过
- 覆盖率达到目标
- 无测试跳过
- 性能测试在时限内完成
