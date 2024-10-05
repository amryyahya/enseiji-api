from flask import Flask, request, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from database import users
from default_categories import DEFAULT_CATEGORIES
from utils import filter_by_date, filter_by_amount, build_pipeline
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
        if user["username"] == username:
            return jsonify({"msg": "username has already exist"}), 400
    user = {
        "username":username,
        "password": generate_password_hash(password),
        "categories":DEFAULT_CATEGORIES,
        "expenses":[],
        "createdDate": datetime.now().isoformat()
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
    if not user:
        return jsonify({"msg": "Invalid username"}), 401
    if not password == password:
        return jsonify({"msg": "invalid password"}), 401
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify({
        'access_token':access_token,
        'refresh_token':refresh_token
    }), 200

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_access_token), 200

################ EXPENSE ROUTE ################################################################
@app.route('/expenses', methods=['GET'])
@jwt_required()
def getExpenses():
    current_user = get_jwt_identity()
    # Pagination
    page = int(request.args.get('page',1))
    limit = int(request.args.get('limit',10))
    skip = (page - 1) * limit
    match_conditions = {}
    # Date range filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date or end_date: match_conditions['expenses.date'] = filter_by_date(start_date, end_date)
    # Amount range filtering
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    if min_amount or max_amount: match_conditions['expenses.amount'] = filter_by_amount(min_amount, max_amount)
    # Category filtering
    categories = request.args.getlist('category') 
    if categories:
        match_conditions['expenses.category'] = {'$in': categories}
    # Sorting
    sort_by = request.args.get('sort_by',"date")
    order = request.args.get('order', 'desc')
    sort_order = 1 if order == 'asc' else -1
    # Querying
    pipeline = build_pipeline(current_user, "expenses", match_conditions, f"expenses.{sort_by}", sort_order, skip, limit) 
    results = users.aggregate(pipeline)
    print(pipeline)
    expenses_list = [result['expenses'] for result in results]
    return jsonify({"expenses": expenses_list}),200

@app.route('/expenses', methods=['POST'])
@jwt_required()
def addExpense():
    current_user = get_jwt_identity()
    data = request.get_json()
    amount = data.get('amount')
    category = data.get('category')
    description = data.get('description')
    date = data.get('date',datetime.now().isoformat())
    newExpense = {
        "_id": str(uuid.uuid4()),  
        "amount": amount,
        "category": category,
        "description": description,
        "date": date 
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
    users.update_one(
        { "username": current_user},
        { "$pull": { "expenses": { "_id": expenseId}}}
    )
    return jsonify(status="expense record deleted"), 200

################ CATEGORY ROUTE ################################################################
@app.route('/categories', methods=['GET'])
@jwt_required()
def getAllCategories():
    current_user = get_jwt_identity()
    user = users.find_one({"username":current_user})
    return jsonify({"categories": user.get("categories")}),200

@app.route('/categories', methods=['POST'])
@jwt_required()
def addCategory():
    current_user = get_jwt_identity()
    data = request.get_json()
    categoryName = data.get('name')
    newCategory = {
        "name": categoryName,
        "date": datetime.now().isoformat()
    }
    users.update_one(
        { "username": current_user },  
        { "$push": { "categories": newCategory } }
    )
    return jsonify(status="new category added"), 200

@app.route('/categories', methods=['DELETE'])
@jwt_required()
def deleteCategory():
    current_user = get_jwt_identity()
    data = request.get_json()
    categoryName = data.get('name')
    users.update_one(
        { "username": current_user},
        { "$pull": { "categories": { "name": categoryName}}}
    )
    return jsonify(status="a category deleted"), 200

if __name__ == '__main__':
    app.run(debug=True)
