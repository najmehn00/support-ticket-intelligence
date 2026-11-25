from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.api.routes.tickets import get_db
from app.main import app


TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/tickets_test"

if not TEST_DATABASE_URL.endswith("/tickets_test"):
    raise RuntimeError("Tests must use tickets_test database")


@asynccontextmanager
async def test_lifespan(_app):
    yield


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    if engine.url.database != "tickets_test":
        raise RuntimeError("Refusing to run tests on a non-test database")

    Base.metadata.create_all(bind=engine)

    routing_sql = Path("database/route_ticket.sql").read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.exec_driver_sql(routing_sql)

    yield engine

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP FUNCTION IF EXISTS route_ticket(UUID, VARCHAR)"
        )

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()

    testing_session = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )()

    try:
        yield testing_session
    finally:
        testing_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan