"""
Patch Applicator

Safely applies remediation patches to CSV files with audit logging.
Enforces policy guardrails before applying changes.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from .schemas import RemediationPatch, PatchApplyResult, PatchProposal
from .policy import RemediationPolicy
from .row_identifier import RowIdentifierGenerator


class PatchApplicator:
    """Apply remediation patches to CSV files"""
    
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.df: Optional[pd.DataFrame] = None
    
    def load_csv(self) -> bool:
        """Load CSV file"""
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def apply_patch(
        self,
        patch: RemediationPatch,
        require_approval: bool = True,
        auto_apply_confidence_threshold: float = 0.9,
        auto_apply_low_risk: bool = False
    ) -> PatchApplyResult:
        """
        Apply patch to CSV with policy enforcement.
        
        Args:
            patch: Remediation patch to apply
            require_approval: Require manual approval for all changes (default True)
            auto_apply_confidence_threshold: Confidence threshold for auto-apply (default 0.9)
            auto_apply_low_risk: Auto-apply low-risk changes (default False)
        
        Returns:
            PatchApplyResult with audit log
        """
        if self.df is None:
            if not self.load_csv():
                return PatchApplyResult(
                    patch_id=patch.patch_id,
                    errors=["Failed to load CSV file"]
                )
        
        applied_changes: List[Dict[str, Any]] = []
        rejected_changes: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        for proposal in patch.tasks:
            try:
                # Find task in patch metadata or load from task_id
                # For now, we'll need to match by row identifier
                # This is simplified - in real implementation, we'd store task mapping
                
                # Validate proposal
                # We need current_value and column from the original task
                # For now, we'll skip validation that requires original task
                # In full implementation, we'd store task mapping in patch metadata
                
                # Find row by identifier (simplified - would need full task context)
                # For now, we'll apply based on proposal metadata if available
                
                # This is a simplified version - full implementation would:
                # 1. Store task mapping in patch metadata
                # 2. Find row by row_identifier
                # 3. Validate proposal against current value
                # 4. Apply if approved
                
                # Placeholder: skip for now, would need task context
                rejected_changes.append({
                    "task_id": proposal.task_id,
                    "reason": "Full implementation requires task context mapping"
                })
                
            except Exception as e:
                errors.append(f"Error processing proposal {proposal.task_id}: {e}")
        
        return PatchApplyResult(
            patch_id=patch.patch_id,
            applied_count=len(applied_changes),
            rejected_count=len(rejected_changes),
            skipped_count=0,
            applied_changes=applied_changes,
            rejected_changes=rejected_changes,
            errors=errors
        )
    
    def apply_patch_with_tasks(
        self,
        patch: RemediationPatch,
        tasks: List[Any],  # List[RemediationTask] - avoiding circular import
        require_approval: bool = True,
        auto_apply_confidence_threshold: float = 0.9,
        auto_apply_low_risk: bool = False
    ) -> PatchApplyResult:
        """
        Apply patch with full task context.
        
        This is the full implementation that uses task context.
        """
        if self.df is None:
            if not self.load_csv():
                return PatchApplyResult(
                    patch_id=patch.patch_id,
                    errors=["Failed to load CSV file"]
                )
        
        # Create task mapping
        task_map = {task.task_id: task for task in tasks}
        
        applied_changes: List[Dict[str, Any]] = []
        rejected_changes: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        for proposal in patch.tasks:
            try:
                # Get original task
                task = task_map.get(proposal.task_id)
                if not task:
                    rejected_changes.append({
                        "task_id": proposal.task_id,
                        "reason": "Task not found"
                    })
                    continue
                
                # Find row by identifier
                row_index = RowIdentifierGenerator.find_row_by_identifier(
                    self.df, task.row_identifier
                )
                if row_index is None:
                    rejected_changes.append({
                        "task_id": proposal.task_id,
                        "reason": "Row not found by identifier"
                    })
                    continue
                
                row = self.df.iloc[row_index]
                current_value = str(row.get(task.column, '')).strip() if pd.notna(row.get(task.column)) else ''
                
                # Validate proposal
                is_valid, error_msg = RemediationPolicy.validate_proposal(
                    proposal, current_value, task.column
                )
                if not is_valid:
                    rejected_changes.append({
                        "task_id": proposal.task_id,
                        "column": task.column,
                        "current_value": current_value,
                        "proposed_value": proposal.proposed_value,
                        "reason": error_msg
                    })
                    continue
                
                # Check if can auto-apply
                can_auto_apply = RemediationPolicy.can_auto_apply(
                    proposal, auto_apply_confidence_threshold
                ) if auto_apply_low_risk else False
                
                if require_approval and not can_auto_apply:
                    # Skip - requires manual approval
                    rejected_changes.append({
                        "task_id": proposal.task_id,
                        "column": task.column,
                        "current_value": current_value,
                        "proposed_value": proposal.proposed_value,
                        "reason": "Requires manual approval",
                        "confidence": proposal.confidence,
                        "risk_level": proposal.risk_level if isinstance(proposal.risk_level, str) else proposal.risk_level.value
                    })
                    continue
                
                # Apply change
                self.df.at[row_index, task.column] = proposal.proposed_value
                
                applied_changes.append({
                    "task_id": proposal.task_id,
                    "column": task.column,
                    "row_index": row_index,
                    "old_value": current_value,
                    "new_value": proposal.proposed_value,
                    "confidence": proposal.confidence,
                    "reasoning": proposal.reasoning,
                    "transformation_type": proposal.transformation_type if isinstance(proposal.transformation_type, str) else proposal.transformation_type.value,
                    "risk_level": proposal.risk_level if isinstance(proposal.risk_level, str) else proposal.risk_level.value,
                    "applied_at": datetime.utcnow().isoformat() + "Z"
                })
                
            except Exception as e:
                errors.append(f"Error processing proposal {proposal.task_id}: {e}")
        
        return PatchApplyResult(
            patch_id=patch.patch_id,
            applied_count=len(applied_changes),
            rejected_count=len(rejected_changes),
            skipped_count=0,
            applied_changes=applied_changes,
            rejected_changes=rejected_changes,
            errors=errors
        )
    
    def save_csv(self, output_path: Path) -> bool:
        """Save modified CSV to file"""
        if self.df is None:
            return False
        try:
            self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

