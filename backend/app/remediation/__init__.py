"""
LLM Remediation Module for ESMA CSV Pipeline

This module provides LLM-assisted remediation for edge cases that cannot be
handled by deterministic cleaning. It uses Deepseek API with fallback to multiple
models and enforces strict guardrails for safety.
"""

from .schemas import (
    RemediationTask,
    RemediationPatch,
    PatchProposal,
    RowIdentifier,
    TaskContext,
    TaskType,
    RiskLevel,
    TransformationType,
    Severity,
)
from .row_identifier import RowIdentifierGenerator
from .tasks import RemediationTaskGenerator
from .policy import RemediationPolicy, AllowedTransformation
from .patch import PatchApplicator
from .llm_client import LLMClient, GeminiLLMClient

__all__ = [
    "RemediationTask",
    "RemediationPatch",
    "PatchProposal",
    "RowIdentifier",
    "TaskContext",
    "TaskType",
    "RiskLevel",
    "TransformationType",
    "Severity",
    "RowIdentifierGenerator",
    "RemediationTaskGenerator",
    "RemediationPolicy",
    "AllowedTransformation",
    "PatchApplicator",
    "LLMClient",
    "GeminiLLMClient",
]

