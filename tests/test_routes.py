import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import jsonify
from app import app, users
import uuid

# Sample user for testing
test_user = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "TestPassword123",
    "categories": [],
    "expenses": []
}

@pytest.fixture
def client():
    client = app.test_client()
    # Clean up database before and after tests
    users.delete_many({})
    # Insert a test user into the collection
    users.insert_one({
        "username": test_user['username'],
        "email": test_user['email'],
        "password": generate_password_hash(test_user['password']),
        "categories": test_user['categories'],
        "expenses": test_user['expenses']
    })
    yield client
    users.delete_many({})

@pytest.fixture
def auth_headers(client):
    """Login and provide JWT token for authentication"""
    response = client.post('/login', json={
        "username": test_user['username'],
        "password": test_user['password']
    })
    access_token = response.get_json()['access_token']
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def refresh_token_headers(client):
    """Provide refresh token for testing"""
    response = client.post('/login', json={
        "username": test_user['username'],
        "password": test_user['password']
    })
    refresh_token = response.get_json()['refresh_token']
    return {"Authorization": f"Bearer {refresh_token}"}

# Test Email and Username Check Routes
def test_check_email(client):
    response = client.post('/check-email', json={"email": test_user['email']})
    assert response.status_code == 200
    assert response.get_json() == {"exist": True}

def test_check_username(client):
    response = client.post('/check-username', json={"username": test_user['username']})
    assert response.status_code == 200
    assert response.get_json() == {"exist": True}

# Test Register Route
def test_register(client):
    new_user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "displayName": "New User",
        "password": "NewUserPassword123"
    }
    response = client.post('/register', json=new_user_data)
    assert response.status_code == 201
    assert response.get_json() == {"msg": "User registered successfully"}

    # Check the user was added to the database
    user = users.find_one({"username": "newuser"})
    assert user is not None

# Test Login Route
def test_login(client):
    response = client.post('/login', json={
        "username": test_user['username'],
        "password": test_user['password']
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'access_token' in json_data
    assert 'refresh_token' in json_data

# Test Refresh Token Route
def test_refresh_token(client, refresh_token_headers):
    response = client.post('/refresh', headers=refresh_token_headers)
    assert response.status_code == 200
    assert 'access_token' in response.get_json()

# Test Logout Route
def test_logout(client, auth_headers):
    response = client.post('/logout', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['msg'] == f"Refresh token for user {test_user['username']} has been successfully revoked"

    # Test that the token is invalid after logout
    response = client.get('/expenses', headers=auth_headers)
    assert response.status_code == 401
    assert response.get_json()['msg'] == "Token has been revoked"

# Test Expense Routes
def test_add_expense(client, auth_headers):
    new_expense = {
        "amount": 50.00,
        "category": "Groceries",
        "description": "Weekly shopping",
        "date": datetime.now().isoformat()
    }
    response = client.post('/expenses', json=new_expense, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['status'] == "expense record added"

    # Check that the expense was added
    user = users.find_one({"username": test_user['username']})
    assert len(user['expenses']) == 1
    assert user['expenses'][0]['amount'] == 50.00

def test_get_expenses(client, auth_headers):
    # Add some expenses for testing
    expenses = [
        {"_id": str(uuid.uuid4()), "amount": 50, "category": "Groceries", "description": "Groceries", "date": datetime.now().isoformat()},
        {"_id": str(uuid.uuid4()), "amount": 20, "category": "Transport", "description": "Taxi", "date": datetime.now().isoformat()},
    ]
    users.update_one({"username": test_user['username']}, {"$set": {"expenses": expenses}})

    # Test retrieving expenses
    response = client.get('/expenses?page=1&limit=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['expenses']) == 2

def test_delete_expense(client, auth_headers):
    expense_to_delete = {"_id": str(uuid.uuid4()), "amount": 100, "category": "Bills", "description": "Electricity", "date": datetime.now().isoformat()}
    users.update_one({"username": test_user['username']}, {"$push": {"expenses": expense_to_delete}})

    # Check that the expense was added
    user = users.find_one({"username": test_user['username']})
    assert len(user['expenses']) == 1

    # Test deleting the expense
    response = client.delete('/expenses', json={"_id": expense_to_delete['_id']}, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['status'] == "expense record deleted"

    # Check that the expense was deleted
    user = users.find_one({"username": test_user['username']})
    assert len(user['expenses']) == 0

# Test Category Routes
def test_add_category(client, auth_headers):
    new_category = {"name": "Entertainment"}
    response = client.post('/categories', json=new_category, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['status'] == "new category added"

    # Check the category was added
    user = users.find_one({"username": test_user['username']})
    assert any(category['name'] == "Entertainment" for category in user['categories'])

def test_get_categories(client, auth_headers):
    response = client.get('/categories', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'categories' in json_data

def test_delete_category(client, auth_headers):
    new_category = {"name": "Entertainment"}
    users.update_one({"username": test_user['username']}, {"$push": {"categories": new_category}})

    # Delete the category
    response = client.delete('/categories', json={"name": "Entertainment"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['status'] == "a category deleted"

    # Check the category was deleted
    user = users.find_one({"username": test_user['username']})
    assert not any(category['name'] == "Entertainment" for category in user['categories'])
