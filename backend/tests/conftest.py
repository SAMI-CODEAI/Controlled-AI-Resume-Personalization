"""
Test fixtures and configuration.
Uses an in-memory SQLite database for testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.skill import Skill
from app.models.project import Project
from app.models.experience import Experience
from app.auth.auth import hash_password, create_access_token

# In-memory SQLite for tests
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id="test-user-id",
        email="test@example.com",
        hashed_password=hash_password("TestPass123"),
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get auth headers for the test user."""
    token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_skills(db_session, test_user):
    """Create sample skills for testing."""
    skills_data = [
        ("Python", "Programming", 5),
        ("JavaScript", "Programming", 4),
        ("React", "Framework", 4),
        ("FastAPI", "Framework", 5),
        ("PostgreSQL", "Database", 4),
        ("Docker", "DevOps", 4),
        ("Git", "Tool", 5),
        ("AWS", "Cloud", 3),
        ("Machine Learning", "AI", 3),
        ("TypeScript", "Programming", 4),
    ]
    skills = []
    for name, category, level in skills_data:
        skill = Skill(user_id=test_user.id, name=name, category=category, proficiency_level=level)
        db_session.add(skill)
        skills.append(skill)
    db_session.commit()
    return skills


@pytest.fixture
def sample_projects(db_session, test_user):
    """Create sample projects for testing."""
    projects = [
        Project(
            user_id=test_user.id,
            title="AI Resume Builder",
            description="Built a resume generation platform using FastAPI and React",
            technologies="Python, FastAPI, React, PostgreSQL",
            impact="Reduced resume creation time by 80%",
            domain="Web Development",
        ),
        Project(
            user_id=test_user.id,
            title="ML Pipeline",
            description="Developed a machine learning pipeline for data processing",
            technologies="Python, Machine Learning, Docker, AWS",
            impact="Processed 1M records daily",
            domain="Machine Learning",
        ),
    ]
    for p in projects:
        db_session.add(p)
    db_session.commit()
    return projects


@pytest.fixture
def sample_experiences(db_session, test_user):
    """Create sample experiences for testing."""
    exp = Experience(
        user_id=test_user.id,
        company="Tech Corp",
        role="Senior Software Engineer",
        description="Led development of microservices architecture",
        technologies="Python, FastAPI, Docker, PostgreSQL",
    )
    db_session.add(exp)
    db_session.commit()
    return [exp]
