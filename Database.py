from pymongo import MongoClient

def get_db():
    uri = "mongodb+srv://jesseku:Fairbank@ia.yjuddkd.mongodb.net/?retryWrites=true&w=majority&appName=IA"
    client = MongoClient(uri)
    return client["IA"]

def get_users_collection():
    return get_db()["users"]

def get_dashboard_collection():
    return get_db()["dashboard_data"]
