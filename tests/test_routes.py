import pytest
from flask import jsonify
from werkzeug.security import generate_password_hash
from app import app, users  # Assuming you have imported app and users collection

# Sample data for testing
test_user = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "TestPassword123"
}

@pytest.fixture
def client():
    client = app.test_client()
    # Remove any existing test users in the collection
    users.delete_many({})
    yield client
    # Clean up after tests
    users.delete_many({})

def test_check_email(client):
    # Insert a test user with the given email
    users.insert_one({"email": test_user['email'], "username": test_user['username'], "password": generate_password_hash(test_user['password'])})
    # Test the check-email route
    response = client.post('/check-email', json={"email": test_user['email']})
    assert response.status_code == 200
    assert response.get_json() == {"exist": True}
    # Test for non-existing email
    response = client.post('/check-email', json={"email": "nonexistent@example.com"})
    assert response.status_code == 200
    assert response.get_json() == {"exist": False}

def test_check_username(client):
    # Insert a test user with the given username
    users.insert_one({"email": test_user['email'], "username": test_user['username'], "password": generate_password_hash(test_user['password'])})
    # Test the check-username route
    response = client.post('/check-username', json={"username": test_user['username']})
    assert response.status_code == 200
    assert response.get_json() == {"exist": True}
    # Test for non-existing username
    response = client.post('/check-username', json={"username": "nonexistentuser"})
    assert response.status_code == 200
    assert response.get_json() == {"exist": False}

def test_register(client):
    # Test valid registration
    response = client.post('/register', json={
        "username": "newuser",
        "email": "newuser@example.com",
        "displayName": "New User",
        "password": "NewUserPassword123"
    })
    assert response.status_code == 201
    assert response.get_json() == {"msg": "User registered successfully"}
    # Test duplicate registration (user already exists)
    response = client.post('/register', json={
        "username": "newuser",
        "email": "newuser@ example.com",
        "displayName": "New User",
        "password": "NewUserPassword123"
    })
    assert response.status_code == 400
    assert response.get_json() == {"msg": "user has already exist"}

def test_login(client):
    # Insert test user for login
    users.insert_one({
        "email": test_user['email'],
        "username": test_user['username'],
        "password": generate_password_hash(test_user['password'])
    })
    # Test successful login
    response = client.post('/login', json={
        "username": test_user['username'],
        "password": test_user['password']
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'access_token' in json_data
    assert 'refresh_token' in json_data
    # Test login with wrong password
    response = client.post('/login', json={
        "username": test_user['username'],
        "password": "WrongPassword"
    })
    assert response.status_code == 401
    assert response.get_json() == {"msg": "invalid password"}
    # Test login with non-existent user
    response = client.post('/login', json={
        "username": "nonexistentuser",
        "password": "password"
    })
    assert response.status_code == 401
    assert response.get_json() == {"msg": "Invalid user"}


def test_refresh(client):
    # Insert test user
    users.insert_one({
        "email": test_user['email'],
        "username": test_user['username'],
        "password": generate_password_hash(test_user['password'])
    })

    # Login to get refresh token
    login_response = client.post('/login', json={
        "username": test_user['username'],
        "password": test_user['password']
    })
    refresh_token = login_response.get_json()['refresh_token']

    # Test refresh with valid refresh token
    response = client.post('/refresh', headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    assert 'access_token' in response.get_json()

    # Test refresh with invalid token
    response = client.post('/refresh', headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 422  # Typical error for malformed or invalid tokens
