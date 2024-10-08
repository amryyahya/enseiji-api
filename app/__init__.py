from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://172.19.27.17:27017/expense-tracker" 
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)
mongo = PyMongo(app)
users = mongo.db.users 
from app import routes  