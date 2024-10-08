class RunConfig:
    MONGO_HOST = '172.19.27.17'
    MONGO_PORT = 27017
    MONGO_DBNAME = 'expense-tracker'
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"

class TestConfig:
    MONGO_HOST = '172.19.27.17'
    MONGO_PORT = 27017
    MONGO_DBNAME = 'expense-tracker-test'
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"
    TESTING = True