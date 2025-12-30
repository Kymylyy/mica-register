"""
Tests for patch application
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
from backend.app.remediation.patch import PatchApplicator
from backend.app.remediation.schemas import (
    RemediationPatch, PatchProposal, RemediationTask,
    TransformationType, RiskLevel, RowIdentifier, TaskContext, TaskType, Severity
)


def create_test_csv(tmp_path: Path) -> Path:
    """Create a test CSV file"""
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({
        'ae_lei': ['LEI123456789012345678'],
        'ae_commercial_name': ['Test Company'],
        'ae_address': ['Test Addres'],  # Missing 's'
        'ac_serviceCode': ['a. description'],
    })
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path


def create_test_task() -> RemediationTask:
    """Create a test remediation task"""
    return RemediationTask(
        task_id="test-task-1",
        task_type=TaskType.ENCODING_FIX,
        row_identifier=RowIdentifier(lei="LEI123456789012345678"),
        column="ae_address",
        current_value="Test Addres",
        issue_description="Encoding issue",
        context=TaskContext(context={"ae_address": "Test Addres", "ae_commercial_name": "Test Company"}),
        severity=Severity.ERROR
    )


def create_test_patch(task: RemediationTask) -> RemediationPatch:
    """Create a test remediation patch"""
    proposal = PatchProposal(
        task_id=task.task_id,
        proposed_value="Test Address",
        confidence=0.95,
        reasoning="Fixed missing 's'",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    return RemediationPatch(
        patch_id="test-patch-1",
        model_name="gemini-3-flash",
        tasks=[proposal]
    )


def test_patch_application(tmp_path):
    """Test that patch is applied correctly"""
    csv_path = create_test_csv(tmp_path)
    task = create_test_task()
    patch = create_test_patch(task)
    
    applicator = PatchApplicator(csv_path)
    result = applicator.apply_patch_with_tasks(
        patch=patch,
        tasks=[task],
        require_approval=False,
        auto_apply_low_risk=True
    )
    
    assert result.applied_count > 0
    assert len(result.applied_changes) > 0
    
    # Verify CSV was modified
    output_path = tmp_path / "output.csv"
    applicator.save_csv(output_path)
    
    df = pd.read_csv(output_path, encoding='utf-8-sig')
    assert df.iloc[0]['ae_address'] == "Test Address"


def test_patch_rejection_forbidden_column(tmp_path):
    """Test that patches to forbidden columns are rejected"""
    csv_path = create_test_csv(tmp_path)
    
    # Create task for LEI column (forbidden)
    task = RemediationTask(
        task_id="test-task-1",
        task_type=TaskType.ENCODING_FIX,
        row_identifier=RowIdentifier(lei="LEI123456789012345678"),
        column="ae_lei",
        current_value="LEI123456789012345678",
        issue_description="Test",
        context=TaskContext(context={}),
        severity=Severity.ERROR
    )
    
    proposal = PatchProposal(
        task_id=task.task_id,
        proposed_value="NEW_LEI",
        confidence=0.95,
        reasoning="Test",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    patch = RemediationPatch(
        patch_id="test-patch-1",
        model_name="gemini-3-flash",
        tasks=[proposal]
    )
    
    applicator = PatchApplicator(csv_path)
    result = applicator.apply_patch_with_tasks(
        patch=patch,
        tasks=[task],
        require_approval=False,
        auto_apply_low_risk=True
    )
    
    assert result.rejected_count > 0
    assert any("forbidden" in str(change.get("reason", "")).lower() 
               for change in result.rejected_changes)


def test_require_approval(tmp_path):
    """Test that require_approval blocks auto-apply"""
    csv_path = create_test_csv(tmp_path)
    task = create_test_task()
    patch = create_test_patch(task)
    
    applicator = PatchApplicator(csv_path)
    result = applicator.apply_patch_with_tasks(
        patch=patch,
        tasks=[task],
        require_approval=True,  # Require approval
        auto_apply_low_risk=False
    )
    
    # Should be rejected because approval is required
    assert result.rejected_count > 0 or result.applied_count == 0

