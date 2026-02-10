"""
Database models for ESMA MiCA registers

Multi-register architecture:
- Base Entity model with common fields
- Extension tables (1:1) for register-specific fields
- CASP has services and passport_countries relationships
"""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Table, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .database import Base
from .config.registers import RegisterType


# ============================================================================
# Association tables for CASP (many-to-many relationships)
# ============================================================================

casp_entity_service = Table(
    'casp_entity_service',
    Base.metadata,
    Column('casp_entity_id', Integer, ForeignKey('casp_entities.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True)
)

casp_entity_passport_country = Table(
    'casp_entity_passport_country',
    Base.metadata,
    Column('casp_entity_id', Integer, ForeignKey('casp_entities.id'), primary_key=True),
    Column('country_id', Integer, ForeignKey('passport_countries.id'), primary_key=True)
)

# Keep old tables for backward compatibility during migration
# These will be dropped after migration completes
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


# ============================================================================
# Base Entity Model (common fields for all registers)
# ============================================================================

class Entity(Base):
    """Base entity model with fields common to all registers"""
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)

    # Register type (CASP, OTHER, ART, EMT, NCASP)
    # Use values_callable to send lowercase values ('casp') to PostgreSQL
    # instead of uppercase enum names ('CASP')
    register_type = Column(
        SQLEnum(RegisterType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        default=RegisterType.CASP
    )

    # Common fields (present in all registers)
    competent_authority = Column(String, index=True)
    home_member_state = Column(String(2), index=True)
    lei_name = Column(String, index=True)  # Index added for search performance
    lei = Column(String, nullable=True, index=True)  # Nullable (NCASP often missing)
    lei_cou_code = Column(String(10))  # Some codes like 'BVI' are longer than 2

    # Fields present in MOST registers (nullable for OTHER/NCASP)
    commercial_name = Column(String, nullable=True, index=True)
    address = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    authorisation_notification_date = Column(Date, nullable=True, index=True)
    last_update = Column(Date, nullable=True)
    comments = Column(Text, nullable=True)

    # Relationships to extension tables (one-to-one)
    casp_entity = relationship("CaspEntity", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    other_entity = relationship("OtherEntity", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    art_entity = relationship("ArtEntity", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    emt_entity = relationship("EmtEntity", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    ncasp_entity = relationship("NcaspEntity", back_populates="entity", uselist=False, cascade="all, delete-orphan")

    # Tags relationship (unchanged)
    tags = relationship("EntityTag", back_populates="entity", cascade="all, delete-orphan")

    # Legacy relationships (for backward compatibility during migration)
    # Will be removed after migration
    services = relationship("Service", secondary=entity_service, back_populates="entities")
    passport_countries = relationship("PassportCountry", secondary=entity_passport_country, back_populates="entities")

    # Computed properties to expose register-specific fields for API serialization
    @property
    def website_platform(self):
        """CASP: website_platform"""
        return self.casp_entity.website_platform if self.casp_entity else None

    @property
    def authorisation_end_date(self):
        """CASP/ART/EMT: authorisation_end_date"""
        if self.casp_entity:
            return self.casp_entity.authorisation_end_date
        elif self.art_entity:
            return self.art_entity.authorisation_end_date
        elif self.emt_entity:
            return self.emt_entity.authorisation_end_date
        return None

    @property
    def white_paper_url(self):
        """OTHER/ART/EMT: white_paper_url"""
        if self.other_entity:
            return self.other_entity.white_paper_url
        elif self.art_entity:
            return self.art_entity.white_paper_url
        elif self.emt_entity:
            return self.emt_entity.white_paper_url
        return None

    @property
    def white_paper_comments(self):
        """OTHER/ART/EMT: white_paper_comments"""
        if self.other_entity:
            return self.other_entity.white_paper_comments
        elif self.art_entity:
            return self.art_entity.white_paper_comments
        elif self.emt_entity:
            return self.emt_entity.white_paper_comments
        return None

    @property
    def white_paper_last_update(self):
        """OTHER/ART/EMT: white_paper_last_update"""
        if self.other_entity:
            return self.other_entity.white_paper_last_update
        elif self.art_entity:
            return self.art_entity.white_paper_last_update
        elif self.emt_entity:
            return self.emt_entity.white_paper_last_update
        return None

    @property
    def lei_casp(self):
        """OTHER: lei_casp (linked CASP LEI)"""
        return self.other_entity.lei_casp if self.other_entity else None

    @property
    def lei_name_casp(self):
        """OTHER: lei_name_casp (linked CASP name)"""
        return self.other_entity.lei_name_casp if self.other_entity else None

    @property
    def offer_countries(self):
        """OTHER: offer_countries (pipe-separated)"""
        return self.other_entity.offer_countries if self.other_entity else None

    @property
    def dti_codes(self):
        """OTHER/EMT: dti_codes (pipe-separated)"""
        if self.other_entity:
            return self.other_entity.dti_codes
        elif self.emt_entity:
            return self.emt_entity.dti_codes
        return None

    @property
    def dti_ffg(self):
        """OTHER/EMT: dti_ffg (DTI FFG code string)"""
        if self.other_entity:
            return self.other_entity.dti_ffg
        elif self.emt_entity:
            return self.emt_entity.dti_ffg
        return None

    @property
    def credit_institution(self):
        """ART: credit_institution (boolean)"""
        return self.art_entity.credit_institution if self.art_entity else None

    @property
    def white_paper_notification_date(self):
        """ART/EMT: white_paper_notification_date"""
        if self.art_entity:
            return self.art_entity.white_paper_notification_date
        elif self.emt_entity:
            return self.emt_entity.white_paper_notification_date
        return None

    @property
    def white_paper_offer_countries(self):
        """ART: white_paper_offer_countries (pipe-separated)"""
        return self.art_entity.white_paper_offer_countries if self.art_entity else None

    @property
    def exemption_48_4(self):
        """EMT: exemption_48_4 (boolean)"""
        return self.emt_entity.exemption_48_4 if self.emt_entity else None

    @property
    def exemption_48_5(self):
        """EMT: exemption_48_5 (boolean)"""
        return self.emt_entity.exemption_48_5 if self.emt_entity else None

    @property
    def authorisation_other_emt(self):
        """EMT: authorisation_other_emt (e.g., 'Electronic money institution')"""
        return self.emt_entity.authorisation_other_emt if self.emt_entity else None

    @property
    def websites(self):
        """NCASP: websites (pipe-separated multiple websites)"""
        return self.ncasp_entity.websites if self.ncasp_entity else None

    @property
    def infringement(self):
        """NCASP: infringement"""
        return self.ncasp_entity.infringement if self.ncasp_entity else None

    @property
    def reason(self):
        """NCASP: reason for non-compliance"""
        return self.ncasp_entity.reason if self.ncasp_entity else None

    @property
    def decision_date(self):
        """NCASP: decision_date"""
        return self.ncasp_entity.decision_date if self.ncasp_entity else None

    def __repr__(self):
        return f"<Entity(id={self.id}, type={self.register_type}, lei={self.lei})>"


# ============================================================================
# Extension Tables (register-specific fields)
# ============================================================================

class CaspEntity(Base):
    """Extension for CASP register (Crypto-Asset Service Providers)"""
    __tablename__ = "casp_entities"

    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)

    # CASP-specific fields
    website_platform = Column(String, nullable=True)
    authorisation_end_date = Column(Date, nullable=True)

    # Relationships
    entity = relationship("Entity", back_populates="casp_entity")
    services = relationship("Service", secondary=casp_entity_service, back_populates="casp_entities")
    passport_countries = relationship("PassportCountry", secondary=casp_entity_passport_country, back_populates="casp_entities")

    def __repr__(self):
        return f"<CaspEntity(id={self.id})>"


class OtherEntity(Base):
    """Extension for OTHER register (White Papers)"""
    __tablename__ = "other_entities"

    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)

    # OTHER-specific fields
    lei_name_casp = Column(String, nullable=True)  # Linked CASP name
    lei_casp = Column(String, nullable=True)  # Linked CASP LEI
    offer_countries = Column(Text, nullable=True)  # Pipe-separated country codes
    dti_ffg = Column(String, nullable=True)  # DTI FFG code (identifier string)
    dti_codes = Column(Text, nullable=True)  # Pipe-separated DTI codes
    white_paper_url = Column(String, nullable=True)
    white_paper_comments = Column(Text, nullable=True)
    white_paper_last_update = Column(Date, nullable=True)

    # Relationship
    entity = relationship("Entity", back_populates="other_entity")

    def __repr__(self):
        return f"<OtherEntity(id={self.id})>"


class ArtEntity(Base):
    """Extension for ART register (Asset-Referenced Tokens)"""
    __tablename__ = "art_entities"

    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)

    # ART-specific fields
    authorisation_end_date = Column(Date, nullable=True)
    credit_institution = Column(Boolean, nullable=True)
    white_paper_url = Column(String, nullable=True)
    white_paper_notification_date = Column(Date, nullable=True)
    white_paper_offer_countries = Column(Text, nullable=True)  # Pipe-separated
    white_paper_comments = Column(Text, nullable=True)
    white_paper_last_update = Column(Date, nullable=True)

    # Relationship
    entity = relationship("Entity", back_populates="art_entity")

    def __repr__(self):
        return f"<ArtEntity(id={self.id})>"


class EmtEntity(Base):
    """Extension for EMT register (E-Money Tokens)"""
    __tablename__ = "emt_entities"

    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)

    # EMT-specific fields
    authorisation_end_date = Column(Date, nullable=True)
    exemption_48_4 = Column(Boolean, nullable=True)  # YES/NO in CSV
    exemption_48_5 = Column(Boolean, nullable=True)  # YES/NO in CSV
    authorisation_other_emt = Column(Text, nullable=True)
    dti_ffg = Column(String, nullable=True)  # DTI FFG code (identifier string)
    dti_codes = Column(Text, nullable=True)  # Pipe-separated
    white_paper_url = Column(String, nullable=True)
    white_paper_notification_date = Column(Date, nullable=True)
    white_paper_comments = Column(Text, nullable=True)
    white_paper_last_update = Column(Date, nullable=True)

    # Relationship
    entity = relationship("Entity", back_populates="emt_entity")

    def __repr__(self):
        return f"<EmtEntity(id={self.id})>"


class NcaspEntity(Base):
    """Extension for NCASP register (Non-Compliant Entities)"""
    __tablename__ = "ncasp_entities"

    id = Column(Integer, ForeignKey('entities.id'), primary_key=True)

    # NCASP-specific fields
    websites = Column(Text, nullable=True)  # Pipe-separated multiple websites
    infringement = Column(String, nullable=True)  # "No" or description
    reason = Column(Text, nullable=True)
    decision_date = Column(Date, nullable=True)
    # Note: comments and last_update are in base Entity (use ae_ prefix in NCASP CSV)

    # Relationship
    entity = relationship("Entity", back_populates="ncasp_entity")

    def __repr__(self):
        return f"<NcaspEntity(id={self.id})>"


# ============================================================================
# Shared Models (used across registers)
# ============================================================================

class Service(Base):
    """MiCA service codes (a-j) - used only by CASP"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)  # a-j
    description = Column(String)

    # Relationships
    casp_entities = relationship("CaspEntity", secondary=casp_entity_service, back_populates="services")

    # Legacy relationship (for backward compatibility during migration)
    entities = relationship("Entity", secondary=entity_service, back_populates="services")

    def __repr__(self):
        return f"<Service(code={self.code})>"


class PassportCountry(Base):
    """Passport countries - used only by CASP"""
    __tablename__ = "passport_countries"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), unique=True, index=True)

    # Relationships
    casp_entities = relationship("CaspEntity", secondary=casp_entity_passport_country, back_populates="passport_countries")

    # Legacy relationship (for backward compatibility during migration)
    entities = relationship("Entity", secondary=entity_passport_country, back_populates="passport_countries")

    def __repr__(self):
        return f"<PassportCountry(code={self.country_code})>"


class EntityTag(Base):
    """Custom tags for entities (unchanged)"""
    __tablename__ = "entity_tags"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), index=True)
    tag_name = Column(String, index=True)
    tag_value = Column(String, nullable=True)

    entity = relationship("Entity", back_populates="tags")

    def __repr__(self):
        return f"<EntityTag(entity_id={self.entity_id}, name={self.tag_name})>"


class RegisterUpdateMetadata(Base):
    """Latest ESMA update date per register."""
    __tablename__ = "register_update_metadata"

    register_type = Column(
        SQLEnum(RegisterType, values_callable=lambda x: [e.value for e in x]),
        primary_key=True,
        nullable=False
    )
    esma_update_date = Column(Date, nullable=False)
