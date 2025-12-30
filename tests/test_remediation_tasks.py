"""
Tests for remediation task generation
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json
from backend.app.remediation.tasks import RemediationTaskGenerator
from backend.app.remediation.schemas import TaskType, Severity


def create_test_csv(tmp_path: Path) -> Path:
    """Create a test CSV file"""
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({
        'ae_lei': ['LEI123456789012345678', 'LEI987654321098765432'],
        'ae_commercial_name': ['Test Company', 'Another Company'],
        'ae_address': ['Test Address', 'Another Address'],
        'ac_serviceCode': ['a. description', 'b. description'],
        'ac_authorisationNotificationDate': ['01/12/2025', '15/11/2025'],
    })
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path


def create_test_validation_report() -> dict:
    """Create a test validation report"""
    return {
        "version": 1,
        "generated_at": "2025-01-01T00:00:00Z",
        "input_file": "test.csv",
        "encoding": {"detected": "utf-8-sig", "confidence": 1.0},
        "stats": {
            "rows_total": 2,
            "rows_parsed": 2,
            "columns": 5,
            "header": ['ae_lei', 'ae_commercial_name', 'ae_address', 'ac_serviceCode', 'ac_authorisationNotificationDate']
        },
        "issues": [
            {
                "severity": "ERROR",
                "code": "ENCODING_ISSUE",
                "message": "Encoding issue detected",
                "column": "ae_address",
                "rows": [2],
                "examples": ["Test Addres"]
            },
            {
                "severity": "WARNING",
                "code": "DATE_NEEDS_NORMALIZATION",
                "message": "Date needs normalization",
                "column": "ac_authorisationNotificationDate",
                "rows": [2],
                "examples": ["15/11/.2025"]
            }
        ]
    }


def test_task_generation(tmp_path):
    """Test that tasks are generated from validation report"""
    csv_path = create_test_csv(tmp_path)
    report = create_test_validation_report()
    
    generator = RemediationTaskGenerator(csv_path)
    tasks = generator.generate_tasks(report, max_tasks=10)
    
    assert len(tasks) > 0
    assert all(task.task_type in [TaskType.ENCODING_FIX, TaskType.DATE_FIX] for task in tasks)
    assert all(task.severity in [Severity.ERROR, Severity.WARNING] for task in tasks)


def test_task_context_minimal(tmp_path):
    """Test that task context is minimal"""
    csv_path = create_test_csv(tmp_path)
    report = create_test_validation_report()
    
    generator = RemediationTaskGenerator(csv_path)
    tasks = generator.generate_tasks(report, max_tasks=10)
    
    for task in tasks:
        # Context should only contain relevant columns
        assert len(task.context.context) > 0
        # Total context length should be reasonable
        total_length = sum(len(str(v)) for v in task.context.context.values())
        assert total_length <= 2000


def test_row_identifier_generated(tmp_path):
    """Test that row identifiers are generated"""
    csv_path = create_test_csv(tmp_path)
    report = create_test_validation_report()
    
    generator = RemediationTaskGenerator(csv_path)
    tasks = generator.generate_tasks(report, max_tasks=10)
    
    for task in tasks:
        assert task.row_identifier is not None
        # Should have LEI or synthetic_id
        assert task.row_identifier.lei or task.row_identifier.synthetic_id


def test_max_tasks_limit(tmp_path):
    """Test that max_tasks limit is respected"""
    csv_path = create_test_csv(tmp_path)
    report = create_test_validation_report()
    
    generator = RemediationTaskGenerator(csv_path)
    tasks = generator.generate_tasks(report, max_tasks=1)
    
    assert len(tasks) <= 1

