import os
import pathlib

_DB_FILE = pathlib.Path(__file__).parent / "test_password.db"
if _DB_FILE.exists():
    _DB_FILE.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["SECRET_KEY"]   = "test-only-secret-do-not-use-in-prod"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from database import Base, get_db, engine
from main import app
from models import User
from auth import hash_password, create_access_token

engine_test = engine  # DATABASE_URL already points to SQLite
from sqlalchemy.orm import sessionmaker
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@event.listens_for(engine_test, "connect")
def _fk_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    try:
        _DB_FILE.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def user_password():
    return "password123"


@pytest.fixture
def test_user(db, user_password):
    u = User(
        nome="Mario",
        cognome="Rossi",
        email="mario@test.com",
        password_hash=hash_password(user_password),
        ruolo="opts",
    )
    db.add(u)
    db.commit()
    uid = u.id
    yield u
    db.query(User).filter(User.id == uid).delete()
    db.commit()


@pytest.fixture
def user_token(test_user):
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
