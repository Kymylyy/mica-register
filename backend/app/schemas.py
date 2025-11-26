from pydantic import BaseModel
from typing import List, Optional
from datetime import date


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
    competent_authority: Optional[str] = None
    home_member_state: Optional[str] = None
    lei_name: Optional[str] = None
    lei: Optional[str] = None
    lei_cou_code: Optional[str] = None
    commercial_name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    website_platform: Optional[str] = None
    authorisation_notification_date: Optional[date] = None
    authorisation_end_date: Optional[date] = None
    comments: Optional[str] = None
    last_update: Optional[date] = None


class Entity(EntityBase):
    id: int
    services: List[Service] = []
    passport_countries: List[PassportCountry] = []
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


