from pymongo import MongoClient

client = MongoClient('mongodb://172.19.27.17:27017/')
db = client['expense-tracker']
users = db['users']