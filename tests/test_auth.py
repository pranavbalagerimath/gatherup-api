import pytest
import bcrypt
from gatherup_api_service import app  # Assuming your Flask app is in a file named app.py
from database_utils import get_sql_database_connection, execute_sql_query, commit
import uuid

# Test user credentials
TEST_USER = {
    "username": "testuser123",
    "email": "testuser123@example.com",
    "password": "TestPassword!123",
    "full_name": "Test User 123"
}


@pytest.fixture
def client():
    """Creates a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def hash_password(password):
    """Helper function to hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def cleanup_test_user(username=TEST_USER["username"]):
    """Removes test user from the database after tests run."""
    execute_sql_query("DELETE FROM Users WHERE username = %s", (username,))
    commit()


def test_register_user(client):
    """Tests the /register API by creating a test user."""

    # Ensure cleanup before test
    cleanup_test_user()

    # Send registration request
    response = client.post("/register", json=TEST_USER)

    assert response.status_code == 201  # Expect success
    # Verify user exists in the database
    cursor = execute_sql_query("SELECT username FROM Users WHERE username = %s", (TEST_USER["username"],))
    assert cursor.fetchone() is not None
    cleanup_test_user()

def test_duplicate_username(client):
    # Insert test user manually
    unique_username = f"testuser_{uuid.uuid4().hex}"
    unique_email = unique_username+'@gmail.com'
    hashed_password = hash_password(TEST_USER["password"])
    execute_sql_query(
        "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
        (unique_username, unique_email, hashed_password)
    )
    commit()

    test_new_user = {
        "username": unique_username,
        "email": unique_email,
        "password": "TestPassword!123",
        "full_name": "Test User 123"
    }
    # Send registration request
    response = client.post("/register", json=test_new_user)
    assert response.status_code == 400
    cleanup_test_user(unique_username)

def test_duplicate_email(client):
    # Insert test user manually
    unique_username = f"testuser_{uuid.uuid4().hex}"
    unique_email = unique_username + '@gmail.com'
    hashed_password = hash_password(TEST_USER["password"])
    execute_sql_query(
        "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
        (unique_username, unique_email, hashed_password)
    )
    commit()

    # Test user credentials
    test_new_user = {
        "username": f"testuser_{uuid.uuid4().hex}",
        "email": unique_email,
        "password": "TestPassword!123",
        "full_name": "Test User 123"
    }

    # Send registration request
    response = client.post("/register", json=test_new_user)
    assert response.status_code == 400
    cleanup_test_user(unique_username)

def test_login_user(client):
    """Tests the /login API using the registered test user."""
    unique_username = f"testuser_{uuid.uuid4().hex}"
    unique_email = unique_username + '@gmail.com'
    # Insert test user manually
    hashed_password = hash_password(TEST_USER["password"])
    execute_sql_query(
        "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
        (unique_username, unique_email, hashed_password)
    )
    commit()

    # Attempt login
    response = client.post("/login", json={"username": unique_username, "password": TEST_USER["password"]})

    assert response.status_code == 200  # Expect success
    assert response.json["message"] == "Login successful"
    cleanup_test_user(unique_username)


def test_invalid_login(client):
    """Tests login with incorrect credentials."""
    unique_username = f"testuser_{uuid.uuid4().hex}"
    unique_email = unique_username + '@gmail.com'
    response = client.post("/login", json={"username": unique_username, "password": "WrongPassword!"})
    assert response.status_code == 401  # Expect unauthorized
    assert response.json["error"] == "Invalid username or password"
    cleanup_test_user(unique_username)

