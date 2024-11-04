from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_cors import CORS
import os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)  
env = os.getenv("FLASK_ENV")
mongo_uri = os.getenv("MONGO_URI")
app.config["MONGO_URI"] = mongo_uri if env == 'PRODUCTION' else mongo_uri + "-test"
print(app.config["MONGO_URI"])
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)
mongo = PyMongo(app)
users = mongo.db.users 
from app import routes  