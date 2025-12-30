"""
Remediation Policy and Guardrails

Enforces allowed transformations and blocks forbidden edits for safety.
"""

from enum import Enum
from typing import Set, Optional, Dict
from .schemas import TaskType, TransformationType, RiskLevel, PatchProposal


class AllowedTransformation(str, Enum):
    """Allowed transformation types with risk levels"""
    ENCODING_FIX = "ENCODING_FIX"
    COUNTRY_NORMALIZE = "COUNTRY_NORMALIZE"
    WEBSITE_FIX = "WEBSITE_FIX"
    DATE_FIX = "DATE_FIX"
    ADDRESS_FIX = "ADDRESS_FIX"


# Risk level mapping
TRANSFORMATION_RISK_LEVELS: Dict[TransformationType, RiskLevel] = {
    TransformationType.ENCODING_FIX: RiskLevel.LOW,
    TransformationType.COUNTRY_NORMALIZE: RiskLevel.LOW,
    TransformationType.WEBSITE_FIX: RiskLevel.LOW,
    TransformationType.DATE_FIX: RiskLevel.MEDIUM,
    TransformationType.ADDRESS_FIX: RiskLevel.MEDIUM,
}

# Forbidden columns - LLM cannot modify these
FORBIDDEN_COLUMNS: Set[str] = {
    'ae_lei',  # LEI cannot be changed (except trivial trimming, which should be deterministic)
}

# Forbidden transformations
FORBIDDEN_TRANSFORMATIONS: Set[TransformationType] = set()  # Can be extended if needed


class RemediationPolicy:
    """Enforces remediation policy and guardrails"""
    
    @staticmethod
    def is_allowed_transformation(transformation_type: TransformationType) -> bool:
        """Check if transformation type is allowed"""
        return transformation_type not in FORBIDDEN_TRANSFORMATIONS
    
    @staticmethod
    def is_allowed_column(column: str) -> bool:
        """Check if column can be modified"""
        return column not in FORBIDDEN_COLUMNS
    
    @staticmethod
    def get_risk_level(transformation_type: TransformationType) -> RiskLevel:
        """Get risk level for transformation type"""
        return TRANSFORMATION_RISK_LEVELS.get(transformation_type, RiskLevel.HIGH)
    
    @staticmethod
    def validate_proposal(proposal: PatchProposal, current_value: str, column: str) -> tuple[bool, Optional[str]]:
        """
        Validate a patch proposal.
        
        Returns:
            (is_valid, error_message)
        """
        # Check if transformation type is allowed
        if not RemediationPolicy.is_allowed_transformation(proposal.transformation_type):
            return False, f"Forbidden transformation type: {proposal.transformation_type}"
        
        # Check if column is allowed
        if not RemediationPolicy.is_allowed_column(column):
            return False, f"Forbidden column: {column}. LLM cannot modify this column."
        
        # Check LEI-specific rules
        if column == 'ae_lei':
            # Only allow trivial trimming (trailing spaces, dots)
            original_trimmed = current_value.strip().rstrip('.')
            proposed_trimmed = proposal.proposed_value.strip().rstrip('.')
            if original_trimmed != proposed_trimmed:
                return False, "LEI value cannot be changed (only trivial trimming allowed, prefer deterministic cleaning)"
        
        # Check confidence threshold
        if proposal.confidence < 0.5:
            return False, f"Confidence too low: {proposal.confidence} (minimum 0.5)"
        
        # Validate risk level matches transformation type
        expected_risk = RemediationPolicy.get_risk_level(proposal.transformation_type)
        if proposal.risk_level != expected_risk:
            # Warning but not blocking - risk level might be adjusted by LLM
            pass
        
        return True, None
    
    @staticmethod
    def can_auto_apply(proposal: PatchProposal, auto_apply_confidence_threshold: float = 0.9) -> bool:
        """
        Check if proposal can be auto-applied based on confidence and risk level.
        
        Args:
            proposal: Patch proposal to check
            auto_apply_confidence_threshold: Minimum confidence for auto-apply (default 0.9)
        
        Returns:
            True if can be auto-applied
        """
        # Only LOW risk transformations can be auto-applied
        if proposal.risk_level != RiskLevel.LOW:
            return False
        
        # Must meet confidence threshold
        if proposal.confidence < auto_apply_confidence_threshold:
            return False
        
        return True

