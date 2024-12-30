from flask import Flask, request, jsonify, redirect
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from app import app, users
from app.utils import filter_by_date, filter_by_amount, build_pipeline, verify_token
from app.default_categories import DEFAULT_CATEGORIES
from bson import ObjectId
import uuid, os, requests, random, string

@app.route('/check-email', methods=['POST'])
def checkEmail():
    try:
        email = request.get_json().get('email')
        if users.count_documents({"email": email}) > 0:
            return jsonify({"exist": True}), 200
        return jsonify({"exist": False}), 200
    except Exception as e:
        print(str(e))
    
@app.route('/check-username', methods=['POST'])
def checkUsername():
    try:
        username = request.get_json().get('username')
        if users.count_documents({"username": username}) > 0:
            return jsonify({"exist": True}), 200
        return jsonify({"exist": False}), 200
    except Exception as e:
        print(str(e))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    displayName = data.get('displayName')
    password = data.get('password')
    if not (username or email) or not password:
        return jsonify({"msg": "Username/Email and password are required"}), 400
    userExist = users.count_documents({"username": username} if username else {"email": email}) > 0
    if userExist:
        return jsonify({"msg": "user has already exist"}), 400
    user = {
        "username":username,
        "email":email,
        "displayName": displayName,
        "password": generate_password_hash(password),
        "categories":DEFAULT_CATEGORIES,
        "expenses":[],
        "blockedTokens":[],
        "createdDate": datetime.now().isoformat()
    }
    
    users.insert_one(user)
    return jsonify({"msg": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not (username or email) or not password:
        return jsonify({"msg": "Username/email and password are required"}), 400
    user = users.find_one(
        {"username": username} if username else {"email": email},
        {"_id": 1, "password": 1}
    )
    if not user:
        return jsonify({"msg": "Invalid user"}), 401
    if not check_password_hash(user["password"],password):
        return jsonify({"msg": "invalid password"}), 401
    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=str(user["_id"]))
    return jsonify({
        'access_token':access_token,
        'refresh_token':refresh_token
    }), 200

@app.route('/oauth/google')
def googleOauth():
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    google_auth_url = (
        f"{AUTH_URL}?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=email%20profile"
    )
    return redirect(google_auth_url)

@app.route('/auth/callback')
def googleOauthCallback():
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    FRONTEND_URL = os.getenv("FRONTEND_URL")  
    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    code = request.args.get('code')
    token_data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }

    token_response = requests.post(TOKEN_URL, data=token_data)
    token_json = token_response.json()
    access_token = token_json.get('access_token')
    user_info_response = requests.get(
        USER_INFO_URL, headers={'Authorization': f'Bearer {access_token}'}
    )
    user_info = user_info_response.json()
    username = user_info['email']
    email = user_info['email']
    displayName = user_info['name']
    password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    user = users.find_one(
        {"username": username} if username else {"email": email},
        {"_id": 1, "password": 1}
    )
    if user:
        refresh_token = create_refresh_token(identity=str(user["_id"]))
        return redirect(f"{FRONTEND_URL}/auth-success?refresh_token={refresh_token}")
    user = {
        "username":username,
        "email":email,
        "displayName": displayName,
        "password": generate_password_hash(password),
        "categories":DEFAULT_CATEGORIES,
        "expenses":[],
        "blockedTokens":[],
        "createdDate": datetime.now().isoformat()
    }
    result = users.insert_one(user)
    user_id = result.inserted_id
    refresh_token = create_refresh_token(identity=str(user_id))
    return redirect(f"{FRONTEND_URL}/auth-success?refresh_token={refresh_token}")

@app.route('/oauth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refreshOauth():
    current_user = get_jwt_identity()
    refresh_jti = get_jwt()['jti']
    if not verify_token(ObjectId(current_user), refresh_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    users.update_one(
        {"_id": ObjectId(current_user)},
        {"$push": {"blockedTokens": refresh_jti}}
    )
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity=current_user)
    return jsonify({
        'access_token':new_access_token,
        'refresh_token':new_refresh_token
    }), 200

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    refresh_jti = get_jwt()['jti'] 
    if not verify_token(ObjectId(current_user), refresh_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    new_access_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_access_token), 200

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    users.update_one(
        {"_id": ObjectId(current_user)},
        {"$push": {"blockedTokens": access_jti}}
    )
    return jsonify(msg=f"Refresh token has been successfully revoked"), 200

@app.route('/logout/refresh', methods=['POST'])
@jwt_required(refresh=True)
def logout_refresh():
    current_user = get_jwt_identity()
    refresh_jti = get_jwt()['jti']
    if not verify_token(ObjectId(current_user), refresh):
        return jsonify({"msg": "Token has been revoked"}), 401
    users.update_one(
        {"_id": ObjectId(current_user)},
        {"$push": {"blockedTokens": refresh_jti}}
    )
    return jsonify(msg=f"Refresh token revoked"), 200

################ EXPENSE ROUTE ################################################################
@app.route('/expenses', methods=['GET'])
@jwt_required()
def getExpenses():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']  
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
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
    pipeline = build_pipeline(ObjectId(current_user), "expenses", match_conditions, f"expenses.{sort_by}", sort_order, skip, limit) 
    results = users.aggregate(pipeline)
    print(pipeline)
    expenses_list = [result['expenses'] for result in results]
    return jsonify({"expenses": expenses_list}),200

@app.route('/expenses', methods=['POST'])
@jwt_required()
def addExpense():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']  
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
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
        { "_id": ObjectId(current_user) },  
        { "$push": { "expenses": newExpense } }
    )
    return jsonify(status="expense record added"), 200

@app.route('/expenses', methods=['DELETE'])
@jwt_required()
def deleteExpense():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']  
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    data = request.get_json()
    expenseId = data.get('_id')
    users.update_one(
        { "_id": ObjectId(current_user)},
        { "$pull": { "expenses": { "_id": expenseId}}}
    )
    return jsonify(status="expense record deleted"), 200

################ CATEGORY ROUTE ################################################################
@app.route('/categories', methods=['GET'])
@jwt_required()
def getAllCategories():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']  
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    user_data = users.find_one(
        {"_id": ObjectId(current_user)},
        {"categories": 1}
    )
    return jsonify({"categories": user_data.get("categories")}), 200

@app.route('/categories', methods=['POST'])
@jwt_required()
def addCategory():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']  
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    data = request.get_json()
    categoryName = data.get('name')
    newCategory = {
        "name": categoryName,
        "date": datetime.now().isoformat()
    }
    users.update_one(
        { "_id": ObjectId(current_user) },  
        { "$push": { "categories": newCategory } }
    )
    return jsonify(status="new category added"), 200

@app.route('/categories', methods=['DELETE'])
@jwt_required()
def deleteCategory():
    current_user = get_jwt_identity()
    access_jti = get_jwt()['jti']  
    if not verify_token(ObjectId(current_user), access_jti):
        return jsonify({"msg": "Token has been revoked"}), 401
    data = request.get_json()
    categoryName = data.get('name')
    users.update_one(
        { "_id": ObjectId(current_user)},
        { "$pull": { "categories": { "name": categoryName}}}
    )
    return jsonify(status="a category deleted"), 200


@app.route('/', methods=['GET'])
def testServer():
    return "<h2>Hello World, Hehe</h2>"