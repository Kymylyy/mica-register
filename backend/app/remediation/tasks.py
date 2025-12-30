"""
Remediation Task Generator

Generates remediation tasks from validation reports.
Maps validation issues to LLM remediation tasks with minimal context.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schemas import (
    RemediationTask,
    TaskType,
    Severity,
    TaskContext,
    RowIdentifier,
)
from .row_identifier import RowIdentifierGenerator


# Mapping from validation issue codes to task types
ISSUE_CODE_TO_TASK_TYPE: Dict[str, TaskType] = {
    'ENCODING_DATA_LOSS': TaskType.ENCODING_FIX,
    'ENCODING_ISSUE': TaskType.ENCODING_FIX,
    'ENCODING_SUSPECT': TaskType.ENCODING_FIX,  # Potential encoding issues
    'DATE_UNPARSABLE': TaskType.DATE_FIX,
    'DATE_NEEDS_NORMALIZATION': TaskType.DATE_FIX,
    'COUNTRY_CODE_INVALID': TaskType.COUNTRY_NORMALIZE,
    'WEBSITE_MULTILINE': TaskType.WEBSITE_FIX,
    'MULTILINE_WEBSITE': TaskType.WEBSITE_FIX,  # Alternative naming
    'ADDRESS_PARSING_ISSUE': TaskType.ADDRESS_FIX,
    'MULTILINE_FIELD': TaskType.ADDRESS_FIX,  # Multiline in address or other fields
    # Note: LEI_INVALID_FORMAT and LEI_DUPLICATE are not mapped because
    # LEI column is forbidden from LLM remediation (handled by deterministic cleaning)
}


# Columns to include in context for each task type
CONTEXT_COLUMNS_BY_TASK_TYPE: Dict[TaskType, List[str]] = {
    TaskType.ENCODING_FIX: ['ae_commercial_name', 'ae_address', 'ae_lei_name', 'ac_competentAuthority', 'ac_comments'],
    TaskType.COUNTRY_NORMALIZE: ['ae_homeMemberState', 'ac_serviceCode_cou'],
    TaskType.WEBSITE_FIX: ['ae_website', 'ae_commercial_name'],
    TaskType.DATE_FIX: ['ac_authorisationNotificationDate', 'ac_authorisationEndDate', 'ac_lastupdate'],
    TaskType.ADDRESS_FIX: ['ae_address', 'ae_website', 'ae_commercial_name'],
}


class RemediationTaskGenerator:
    """Generate remediation tasks from validation report"""
    
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
    
    def generate_tasks(self, validation_report: Dict[str, Any], max_tasks: int = 50) -> List[RemediationTask]:
        """
        Generate remediation tasks from validation report.
        
        Args:
            validation_report: Validation report dictionary
            max_tasks: Maximum number of tasks to generate
        
        Returns:
            List of remediation tasks
        """
        if self.df is None:
            if not self.load_csv():
                return []
        
        tasks: List[RemediationTask] = []
        issues = validation_report.get('issues', [])
        
        for issue in issues:
            if len(tasks) >= max_tasks:
                break
            
            # Only process ERROR and WARNING severity
            severity_str = issue.get('severity', '').upper()
            if severity_str not in ['ERROR', 'WARNING']:
                continue
            
            severity = Severity.ERROR if severity_str == 'ERROR' else Severity.WARNING
            
            # Map issue code to task type
            issue_code = issue.get('code', '')
            task_type = ISSUE_CODE_TO_TASK_TYPE.get(issue_code)
            if not task_type:
                continue  # Skip issues we don't know how to handle
            
            # Get column and rows
            column = issue.get('column')
            if not column:
                continue
            
            rows = issue.get('rows', [])
            examples = issue.get('examples', [])
            
            # Generate task for each affected row
            for row_num in rows[:5]:  # Limit to first 5 examples per issue
                if len(tasks) >= max_tasks:
                    break
                
                # Convert 1-based row number to 0-based index
                row_index = row_num - 2  # -2 because header is row 1, data starts at row 2
                if row_index < 0 or row_index >= len(self.df):
                    continue
                
                row = self.df.iloc[row_index]
                
                # Get current value
                current_value = str(row.get(column, '')).strip() if pd.notna(row.get(column)) else ''
                if not current_value:
                    continue  # Skip empty values
                
                # Generate row identifier
                row_identifier = RowIdentifierGenerator.from_row(row, row_index)
                
                # Build minimal context
                context_columns = CONTEXT_COLUMNS_BY_TASK_TYPE.get(task_type, [column])
                context_data = {}
                for col in context_columns:
                    if col in self.df.columns:
                        value = str(row.get(col, '')).strip() if pd.notna(row.get(col)) else ''
                        # Cap at 500 chars per column
                        if len(value) > 500:
                            value = value[:500] + '...'
                        context_data[col] = value
                
                # If context is empty, add at least the problem column
                if not context_data:
                    context_data[column] = current_value[:500]
                
                task_context = TaskContext(context=context_data)
                
                # Create task
                task = RemediationTask(
                    task_type=task_type,
                    row_identifier=row_identifier,
                    column=column,
                    current_value=current_value[:1000],  # Cap at 1000 chars
                    issue_description=issue.get('message', ''),
                    context=task_context,
                    severity=severity,
                    metadata={
                        'issue_code': issue_code,
                        'row_number': row_num,
                        'row_index': row_index,
                        'example': examples[0] if examples else None,
                    }
                )
                
                tasks.append(task)
        
        return tasks

