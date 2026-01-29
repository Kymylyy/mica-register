from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from enum import Enum


class RegisterTypeEnum(str, Enum):
    """Register type enum for API responses"""
    CASP = "casp"
    OTHER = "other"
    ART = "art"
    EMT = "emt"
    NCASP = "ncasp"


class ServiceBase(BaseModel):
    code: str
    description: Optional[str] = None


class Service(ServiceBase):
    id: int

    class Config:
        from_attributes = True


class PassportCountryBase(BaseModel):
    country_code: str


class PassportCountry(PassportCountryBase):
    id: int

    class Config:
        from_attributes = True


class EntityTagBase(BaseModel):
    tag_name: str
    tag_value: Optional[str] = None


class EntityTag(EntityTagBase):
    id: int
    entity_id: int

    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    """Base entity schema with common fields for all registers"""
    # Register type
    register_type: RegisterTypeEnum = RegisterTypeEnum.CASP  # Default for backward compatibility

    # Common fields (all registers)
    competent_authority: Optional[str] = None
    home_member_state: Optional[str] = None
    lei_name: Optional[str] = None
    lei: Optional[str] = None
    lei_cou_code: Optional[str] = None

    # Fields present in most registers (nullable)
    commercial_name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    authorisation_notification_date: Optional[date] = None
    last_update: Optional[date] = None
    comments: Optional[str] = None

    # CASP-specific fields (populated from casp_entity relationship)
    # Kept here for backward compatibility - will be None for non-CASP registers
    website_platform: Optional[str] = None
    authorisation_end_date: Optional[date] = None

    # OTHER-specific fields (populated from other_entity relationship)
    # Will be None for non-OTHER registers
    white_paper_url: Optional[str] = None
    white_paper_comments: Optional[str] = None
    white_paper_last_update: Optional[date] = None
    lei_casp: Optional[str] = None
    lei_name_casp: Optional[str] = None
    offer_countries: Optional[str] = None  # Pipe-separated
    dti_codes: Optional[str] = None  # Pipe-separated
    dti_ffg: Optional[bool] = None

    # ART-specific fields (populated from art_entity relationship)
    # Will be None for non-ART registers
    credit_institution: Optional[bool] = None
    white_paper_notification_date: Optional[date] = None
    white_paper_offer_countries: Optional[str] = None  # Pipe-separated

    # EMT-specific fields (populated from emt_entity relationship)
    # Will be None for non-EMT registers
    exemption_48_4: Optional[bool] = None
    exemption_48_5: Optional[bool] = None
    authorisation_other_emt: Optional[str] = None

    # NCASP-specific fields (populated from ncasp_entity relationship)
    # Will be None for non-NCASP registers
    websites: Optional[str] = None  # Pipe-separated multiple websites
    infringement: Optional[str] = None
    reason: Optional[str] = None
    decision_date: Optional[date] = None


class Entity(EntityBase):
    """Full entity schema with all relationships

    Note: services and passport_countries are only populated for CASP entities
    """
    id: int
    services: List[Service] = []  # CASP only
    passport_countries: List[PassportCountry] = []  # CASP only
    tags: List[EntityTag] = []

    class Config:
        from_attributes = True


class EntityCreate(EntityBase):
    services: List[str] = []
    passport_countries: List[str] = []


class TagCreate(BaseModel):
    tag_name: str
    tag_value: Optional[str] = None


class EntityUpdate(BaseModel):
    comments: Optional[str] = None


