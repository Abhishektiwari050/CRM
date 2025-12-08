"""
Pytest configuration and fixtures for API tests
"""
import pytest
from fastapi.testclient import TestClient
from typing import Generator
import os

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["USE_DEMO"] = "1"
os.environ["JWT_SECRET"] = "test-secret-key-for-pytest-only"

from ..main import app
from ..utils.security import create_token, hash_password

@pytest.fixture(scope="session")
def test_app():
    """
    Create a test FastAPI application
    """
    return app

@pytest.fixture(scope="function")
def client(test_app) -> Generator:
    """
    Create a test client for the application
    """
    with TestClient(test_app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def test_user():
    """
    Test user data
    """
    return {
        "id": "test-user-123",
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test Password123!",
        "password_hash": hash_password("TestPassword123!"),
        "role": "employee"
    }

@pytest.fixture(scope="session")
def test_manager():
    """
    Test manager user data
    """
    return {
        "id": "test-manager-456",
        "name": "Test Manager",
        "email": "manager@example.com",
        "password": "ManagerPass123!",
        "password_hash": hash_password("ManagerPass123!"),
        "role": "manager"
    }

@pytest.fixture(scope="session")
def test_admin():
    """
    Test admin user data
    """
    return {
        "id": "test-admin-789",
        "name": "Test Admin",
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "password_hash": hash_password("AdminPass123!"),
        "role": "admin"
    }

@pytest.fixture(scope="function")
def auth_token_employee(test_user):
    """
    Generate a valid JWT token for employee user
    """
    return create_token(test_user["id"], test_user["role"])

@pytest.fixture(scope="function")
def auth_token_manager(test_manager):
    """
    Generate a valid JWT token for manager user
    """
    return create_token(test_manager["id"], test_manager["role"])

@pytest.fixture(scope="function")
def auth_token_admin(test_admin):
    """
    Generate a valid JWT token for admin user
    """
    return create_token(test_admin["id"], test_admin["role"])

@pytest.fixture(scope="function")
def auth_headers_employee(auth_token_employee):
    """
    Authorization headers for employee
    """
    return {"Authorization": f"Bearer {auth_token_employee}"}

@pytest.fixture(scope="function")
def auth_headers_manager(auth_token_manager):
    """
    Authorization headers for manager
    """
    return {"Authorization": f"Bearer {auth_token_manager}"}

@pytest.fixture(scope="function")
def auth_headers_admin(auth_token_admin):
    """
    Authorization headers for admin
    """
    return {"Authorization": f"Bearer {auth_token_admin}"}
