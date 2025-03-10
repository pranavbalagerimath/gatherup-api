import pytest
import bcrypt
from gatherup_api_service import app  # Assuming your Flask app is in a file named app.py
from database_utils import get_sql_database_connection, execute_sql_query, commit

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


def cleanup_test_user():
    """Removes test user from the database after tests run."""
    execute_sql_query("DELETE FROM Users WHERE username = %s", (TEST_USER["username"],))
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

def test_duplicate_username(client):
    # Insert test user manually
    hashed_password = hash_password(TEST_USER["password"])
    execute_sql_query(
        "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
        (TEST_USER["username"], TEST_USER["email"], hashed_password)
    )
    commit()

    # Send registration request
    response = client.post("/register", json=TEST_USER)
    assert response.status_code == 400

def test_duplicate_email(client):
    # Insert test user manually
    hashed_password = hash_password(TEST_USER["password"])
    execute_sql_query(
        "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
        (TEST_USER["username"], TEST_USER["email"], hashed_password)
    )
    commit()

    # Test user credentials
    test_new_user = {
        "username": TEST_USER["username"] + '_new',
        "email": TEST_USER["email"],
        "password": "TestPassword!123",
        "full_name": "Test User 123"
    }

    # Send registration request
    response = client.post("/register", json=test_new_user)
    assert response.status_code == 400

def test_login_user(client):
    """Tests the /login API using the registered test user."""

    # Insert test user manually
    hashed_password = hash_password(TEST_USER["password"])
    execute_sql_query(
        "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)",
        (TEST_USER["username"], TEST_USER["email"], hashed_password)
    )
    commit()

    # Attempt login
    response = client.post("/login", json={"username": TEST_USER["username"], "password": TEST_USER["password"]})

    assert response.status_code == 200  # Expect success
    assert response.json["message"] == "Login successful"


def test_invalid_login(client):
    """Tests login with incorrect credentials."""

    response = client.post("/login", json={"username": TEST_USER["username"], "password": "WrongPassword!"})

    assert response.status_code == 401  # Expect unauthorized
    assert response.json["error"] == "Invalid username or password"


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Automatically cleans up test users after all tests are done."""
    yield
    cleanup_test_user()
