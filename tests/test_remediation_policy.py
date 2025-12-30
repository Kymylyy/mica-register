"""
Tests for remediation policy and guardrails
"""

import pytest
from backend.app.remediation.policy import RemediationPolicy, AllowedTransformation
from backend.app.remediation.schemas import PatchProposal, TransformationType, RiskLevel


def test_allowed_transformation():
    """Test that allowed transformations pass"""
    assert RemediationPolicy.is_allowed_transformation(TransformationType.ENCODING_FIX)
    assert RemediationPolicy.is_allowed_transformation(TransformationType.COUNTRY_NORMALIZE)
    assert RemediationPolicy.is_allowed_transformation(TransformationType.WEBSITE_FIX)


def test_forbidden_column():
    """Test that forbidden columns are blocked"""
    assert not RemediationPolicy.is_allowed_column('ae_lei')
    assert RemediationPolicy.is_allowed_column('ae_address')
    assert RemediationPolicy.is_allowed_column('ae_commercial_name')


def test_lei_change_blocked():
    """Test that LEI value changes are blocked"""
    proposal = PatchProposal(
        task_id="test-1",
        proposed_value="NEW_LEI_VALUE",
        confidence=0.95,
        reasoning="Test",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    is_valid, error = RemediationPolicy.validate_proposal(
        proposal, "OLD_LEI_VALUE", "ae_lei"
    )
    
    assert not is_valid
    # LEI column is completely forbidden, so it's blocked at column level
    assert "forbidden" in error.lower() or "cannot modify" in error.lower()


def test_lei_trimming_allowed():
    """Test that LEI column is completely forbidden (even trimming)"""
    proposal = PatchProposal(
        task_id="test-1",
        proposed_value="LEI_VALUE",
        confidence=0.95,
        reasoning="Trimmed trailing dot",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    is_valid, error = RemediationPolicy.validate_proposal(
        proposal, "LEI_VALUE.", "ae_lei"
    )
    
    # LEI column is completely forbidden - even trimming should be blocked
    # (deterministic cleaning should handle trimming)
    assert not is_valid
    assert "forbidden" in error.lower() or "cannot modify" in error.lower()


def test_low_confidence_blocked():
    """Test that low confidence proposals are blocked"""
    proposal = PatchProposal(
        task_id="test-1",
        proposed_value="fixed_value",
        confidence=0.3,  # Too low
        reasoning="Test",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    is_valid, error = RemediationPolicy.validate_proposal(
        proposal, "old_value", "ae_address"
    )
    
    assert not is_valid
    assert "Confidence too low" in error


def test_auto_apply_low_risk():
    """Test auto-apply logic for low-risk transformations"""
    proposal_low = PatchProposal(
        task_id="test-1",
        proposed_value="fixed",
        confidence=0.95,
        reasoning="Test",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    proposal_medium = PatchProposal(
        task_id="test-2",
        proposed_value="fixed",
        confidence=0.95,
        reasoning="Test",
        transformation_type=TransformationType.DATE_FIX,
        risk_level=RiskLevel.MEDIUM
    )
    
    assert RemediationPolicy.can_auto_apply(proposal_low, 0.9)
    assert not RemediationPolicy.can_auto_apply(proposal_medium, 0.9)


def test_auto_apply_confidence_threshold():
    """Test that confidence threshold is enforced"""
    proposal = PatchProposal(
        task_id="test-1",
        proposed_value="fixed",
        confidence=0.85,  # Below threshold
        reasoning="Test",
        transformation_type=TransformationType.ENCODING_FIX,
        risk_level=RiskLevel.LOW
    )
    
    assert not RemediationPolicy.can_auto_apply(proposal, 0.9)
    assert RemediationPolicy.can_auto_apply(proposal, 0.8)

