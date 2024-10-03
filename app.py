from flask import Flask, request, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from database import users
from default_categories import DEFAULT_CATEGORIES
import uuid

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)
allUsers = users.find()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400
    for user in allUsers:
        print(user["username"])
        if user["username"] == username:
            return jsonify({"msg": "username has already exist"}), 400
    user = {
        "username":username,
        "password":password,
        "categories":DEFAULT_CATEGORIES,
        "expenses":[]
    }
    users.insert_one(user)
    return jsonify({"msg": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400
    user = users.find_one({"username":username})
    if not user or not password == password:
        return jsonify({"msg": "Invalid username or password"}), 401
    # Create a new access token
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

# protected-demo
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 2

################ EXPENSE ROUTE ################################################################
@app.route('/expenses', methods=['GET'])
@jwt_required()
def getAllExpenses():
    current_user = get_jwt_identity()
    user = users.find_one({"username":current_user})
    return jsonify({"expenses": user.get("expenses")}),200

@app.route('/expenses', methods=['POST'])
@jwt_required()
def addExpense():
    current_user = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount')
    category = data.get('category')
    description = data.get('description')
    newExpense = {
        "_id": str(uuid.uuid4()),  
        "amount": amount,
        "category": category,
        "description": description,
        "date": datetime.now().isoformat()  
    }
    users.update_one(
        { "username": current_user },  
        { "$push": { "expenses": newExpense } }
    )
    return jsonify(status="expense record added"), 200

@app.route('/expenses', methods=['DELETE'])
@jwt_required()
def deleteExpense():
    current_user = get_jwt_identity()
    data = request.get_json()
    expenseId = data.get('_id')
    print(expenseId)
    users.update_one(
        { "username": current_user},
        { "$pull": { "expenses": { "_id": expenseId}}}
    )
    return jsonify(status="expense record deleted"), 200

if __name__ == '__main__':
    app.run(debug=True)
