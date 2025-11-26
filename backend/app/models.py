from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

# Association tables for many-to-many relationships
entity_service = Table(
    'entity_service',
    Base.metadata,
    Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True)
)

entity_passport_country = Table(
    'entity_passport_country',
    Base.metadata,
    Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True),
    Column('country_id', Integer, ForeignKey('passport_countries.id'), primary_key=True)
)


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    competent_authority = Column(String, index=True)
    home_member_state = Column(String(2), index=True)
    lei_name = Column(String)
    lei = Column(String, unique=True, index=True)
    lei_cou_code = Column(String(2))
    commercial_name = Column(String, index=True)
    address = Column(Text)
    website = Column(String)
    website_platform = Column(String)
    authorisation_notification_date = Column(Date, index=True)
    authorisation_end_date = Column(Date, nullable=True)
    comments = Column(Text, nullable=True)
    last_update = Column(Date)

    # Relationships
    services = relationship("Service", secondary=entity_service, back_populates="entities")
    passport_countries = relationship("PassportCountry", secondary=entity_passport_country, back_populates="entities")
    tags = relationship("EntityTag", back_populates="entity", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(String)

    entities = relationship("Entity", secondary=entity_service, back_populates="services")


class PassportCountry(Base):
    __tablename__ = "passport_countries"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), unique=True, index=True)

    entities = relationship("Entity", secondary=entity_passport_country, back_populates="passport_countries")


class EntityTag(Base):
    __tablename__ = "entity_tags"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    tag_name = Column(String, index=True)
    tag_value = Column(String, nullable=True)

    entity = relationship("Entity", back_populates="tags")


