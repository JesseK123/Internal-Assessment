import hashlib
import Database

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    users = get_users_collection()
    user = users.find_one({"username": username, "password": hash_password(password)})
    return user is not None

def user_exists(username):
    users = get_users_collection()
    return users.find_one({"username": username}) is not None

def register_user(username, password, email=None):
    users = get_users_collection()
    if user_exists(username):
        return False  # Already exists
    users.insert_one({
        "username": username,
        "password": hash_password(password),
        "email": email or "",
        "role": "user"
    })
    return True
