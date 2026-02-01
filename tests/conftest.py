"""
Pytest configuration and fixtures for MiCA Register testing.

IMPORTANT TECHNICAL NOTES:
1. SQLite in-memory + FastAPI TestClient: Use StaticPool and check_same_thread=False
   to share DB between threads.
2. import_csv_to_db() commits: Can't rollback, so we explicitly clear tables before each test.
3. CSV fixtures must be "cleaned" (no BOM, proper UTF-8 encoding).
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.database import Base
from backend.app.models import (
    Entity, Service, PassportCountry, EntityTag,
    CaspEntity, OtherEntity, ArtEntity, EmtEntity, NcaspEntity,
    casp_entity_service, casp_entity_passport_country,
    entity_service, entity_passport_country
)
from backend.app.main import app
from backend.app.config.registers import RegisterType


@pytest.fixture(scope="session")
def test_engine():
    """
    In-memory SQLite engine for tests.

    IMPORTANT: Use StaticPool and check_same_thread=False
    so TestClient (which may use threads) can share the DB.
    """
    engine = create_engine(
        "sqlite://",  # in-memory (not ":memory:")
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Fresh DB session for each test.

    IMPORTANT: import_csv_to_db() commits, so we can't use rollback.
    Instead, we explicitly clear all tables before each test.
    """
    Session = sessionmaker(bind=test_engine)
    session = Session()

    # Clear all tables before each test
    # NOTE: Order matters due to foreign keys
    session.execute(casp_entity_service.delete())
    session.execute(casp_entity_passport_country.delete())
    session.execute(entity_service.delete())
    session.execute(entity_passport_country.delete())
    session.query(EntityTag).delete()
    session.query(Service).delete()
    session.query(PassportCountry).delete()
    session.query(CaspEntity).delete()
    session.query(OtherEntity).delete()
    session.query(ArtEntity).delete()
    session.query(EmtEntity).delete()
    session.query(NcaspEntity).delete()
    session.query(Entity).delete()
    session.commit()

    yield session

    session.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client with DB session override"""
    from backend.app.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# CSV Fixtures
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "test_csvs"


@pytest.fixture
def casp_sample_csv():
    """Path to CASP sample CSV"""
    return FIXTURE_DIR / "casp_sample.csv"


@pytest.fixture
def other_sample_csv():
    """Path to OTHER sample CSV"""
    return FIXTURE_DIR / "other_sample.csv"


@pytest.fixture
def art_sample_csv():
    """Path to ART sample CSV"""
    return FIXTURE_DIR / "art_sample.csv"


@pytest.fixture
def emt_sample_csv():
    """Path to EMT sample CSV"""
    return FIXTURE_DIR / "emt_sample.csv"


@pytest.fixture
def ncasp_sample_csv():
    """Path to NCASP sample CSV"""
    return FIXTURE_DIR / "ncasp_sample.csv"


@pytest.fixture
def db_with_casp_data(db_session, casp_sample_csv):
    """Database with loaded CASP data"""
    from backend.app.import_csv import import_csv_to_db

    import_csv_to_db(db_session, str(casp_sample_csv), RegisterType.CASP)
    return db_session


@pytest.fixture
def db_with_other_data(db_session, other_sample_csv):
    """Database with loaded OTHER data"""
    from backend.app.import_csv import import_csv_to_db

    import_csv_to_db(db_session, str(other_sample_csv), RegisterType.OTHER)
    return db_session


@pytest.fixture
def db_with_art_data(db_session, art_sample_csv):
    """Database with loaded ART data"""
    from backend.app.import_csv import import_csv_to_db

    import_csv_to_db(db_session, str(art_sample_csv), RegisterType.ART)
    return db_session


@pytest.fixture
def db_with_emt_data(db_session, emt_sample_csv):
    """Database with loaded EMT data"""
    from backend.app.import_csv import import_csv_to_db

    import_csv_to_db(db_session, str(emt_sample_csv), RegisterType.EMT)
    return db_session


@pytest.fixture
def db_with_ncasp_data(db_session, ncasp_sample_csv):
    """Database with loaded NCASP data"""
    from backend.app.import_csv import import_csv_to_db

    import_csv_to_db(db_session, str(ncasp_sample_csv), RegisterType.NCASP)
    return db_session
