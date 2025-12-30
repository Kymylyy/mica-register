"""
Row Identifier for Stable Row Identification

Provides stable row identification that survives merge/dedup operations.
Uses LEI as primary key, with fallback to composite keys or synthetic IDs.
"""

import hashlib
from typing import Optional, Dict, Any
import pandas as pd
from .schemas import RowIdentifier


class RowIdentifierGenerator:
    """Generate stable row identifiers for CSV rows"""
    
    @staticmethod
    def from_row(row: pd.Series, row_index: int) -> RowIdentifier:
        """
        Generate stable row identifier from CSV row.
        
        Strategy:
        1. Primary: LEI (if unique)
        2. Fallback: LEI + competent_authority + service_country (for duplicate LEI)
        3. Last resort: synthetic_id (hash of key fields)
        """
        lei = str(row.get('ae_lei', '')).strip() if pd.notna(row.get('ae_lei')) else None
        competent_authority = str(row.get('ae_competentAuthority', '')).strip() if pd.notna(row.get('ae_competentAuthority')) else None
        service_country = str(row.get('ac_serviceCode_cou', '')).strip() if pd.notna(row.get('ac_serviceCode_cou')) else None
        
        # If LEI exists, use it (with optional composite key for duplicates)
        if lei and lei != '' and lei.lower() != 'nan':
            return RowIdentifier(
                lei=lei,
                competent_authority=competent_authority,
                service_country=service_country,
                synthetic_id=None
            )
        
        # Last resort: generate synthetic ID from key fields
        key_fields = [
            str(row.get('ae_lei_name', '')),
            str(row.get('ae_commercial_name', '')),
            str(row.get('ae_competentAuthority', '')),
            str(row.get('ae_homeMemberState', '')),
            str(row_index)
        ]
        key_string = '|'.join(key_fields)
        synthetic_id = hashlib.sha256(key_string.encode('utf-8')).hexdigest()[:16]
        
        return RowIdentifier(
            lei=None,
            competent_authority=competent_authority,
            service_country=service_country,
            synthetic_id=synthetic_id
        )
    
    @staticmethod
    def find_row_by_identifier(df: pd.DataFrame, identifier: RowIdentifier) -> Optional[int]:
        """
        Find row index in DataFrame by identifier.
        Returns row index (0-based) or None if not found.
        """
        # Try LEI first
        if identifier.lei:
            matches = df[df['ae_lei'].astype(str).str.strip() == identifier.lei]
            if len(matches) == 1:
                return matches.index[0]
            elif len(matches) > 1:
                # Multiple matches - use composite key
                if identifier.competent_authority and identifier.service_country:
                    matches = matches[
                        (matches['ae_competentAuthority'].astype(str).str.strip() == identifier.competent_authority) &
                        (matches['ac_serviceCode_cou'].astype(str).str.strip() == identifier.service_country)
                    ]
                    if len(matches) == 1:
                        return matches.index[0]
        
        # Try synthetic ID (would need to be stored in CSV or recalculated)
        # For now, return None if not found by LEI
        return None

