"""
Pydantic schemas for LLM Remediation

Defines data structures for remediation tasks, patches, and related metadata.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid


class TaskType(str, Enum):
    """Types of remediation tasks"""
    ENCODING_FIX = "ENCODING_FIX"
    COUNTRY_NORMALIZE = "COUNTRY_NORMALIZE"
    WEBSITE_FIX = "WEBSITE_FIX"
    DATE_FIX = "DATE_FIX"
    ADDRESS_FIX = "ADDRESS_FIX"


class RiskLevel(str, Enum):
    """Risk levels for transformations"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TransformationType(str, Enum):
    """Types of transformations allowed"""
    ENCODING_FIX = "ENCODING_FIX"
    COUNTRY_NORMALIZE = "COUNTRY_NORMALIZE"
    WEBSITE_FIX = "WEBSITE_FIX"
    DATE_FIX = "DATE_FIX"
    ADDRESS_FIX = "ADDRESS_FIX"


class Severity(str, Enum):
    """Issue severity levels"""
    ERROR = "ERROR"
    WARNING = "WARNING"


class RowIdentifier(BaseModel):
    """Stable row identification"""
    lei: Optional[str] = None
    competent_authority: Optional[str] = None
    service_country: Optional[str] = None
    synthetic_id: Optional[str] = None  # Hash-based fallback
    
    def to_key(self) -> str:
        """Convert to stable key string"""
        if self.lei:
            if self.competent_authority and self.service_country:
                return f"{self.lei}|{self.competent_authority}|{self.service_country}"
            return self.lei
        if self.synthetic_id:
            return self.synthetic_id
        return "unknown"


class TaskContext(BaseModel):
    """Minimal context for LLM (only needed columns, capped lengths)"""
    context: Dict[str, str] = Field(
        default_factory=dict,
        description="Minimal row data: selected columns only, max 500 chars per column"
    )
    
    @field_validator('context')
    @classmethod
    def validate_context_length(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Ensure context is within limits"""
        total_length = sum(len(str(val)) for val in v.values())
        if total_length > 2000:
            # Truncate if needed
            truncated = {}
            current_length = 0
            for key, value in v.items():
                val_str = str(value)
                if current_length + len(val_str) > 2000:
                    remaining = 2000 - current_length
                    truncated[key] = val_str[:remaining] + "..."
                    break
                truncated[key] = val_str
                current_length += len(val_str)
            return truncated
        return v


class RemediationTask(BaseModel):
    """Single remediation task from validation report"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    row_identifier: RowIdentifier
    column: str
    current_value: str = Field(max_length=1000)
    issue_description: str
    context: TaskContext
    severity: Severity
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class PatchProposal(BaseModel):
    """Single proposal from LLM"""
    task_id: str
    proposed_value: str = Field(max_length=1000)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(max_length=500)
    transformation_type: TransformationType
    risk_level: RiskLevel
    
    class Config:
        use_enum_values = True


class RemediationPatch(BaseModel):
    """Patch with LLM proposals"""
    patch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_provider: str = "deepseek"
    model_name: str
    tasks: List[PatchProposal] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class PatchApplyResult(BaseModel):
    """Result of applying a patch"""
    patch_id: str
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    applied_count: int = 0
    rejected_count: int = 0
    skipped_count: int = 0
    applied_changes: List[Dict[str, Any]] = Field(default_factory=list)
    rejected_changes: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

