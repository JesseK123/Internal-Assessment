import hashlib
import os
from datetime import datetime, timedelta
import secrets
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import streamlit as st


class DatabaseManager:
    """Handles MongoDB connections and operations"""

    def __init__(self):
        self._client = None
        self._db = None

    @property
    def client(self):
        if self._client is None:
            try:
                # Get connection string from environment variable
                uri = os.getenv("MONGODB_URI")
                if not uri:
                    st.error(
                        "MongoDB connection string not found. Please set MONGODB_URI environment variable."
                    )
                    return None

                self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                # Test connection
                self._client.server_info()
            except ConnectionFailure:
                st.error("Failed to connect to MongoDB. Please check your connection.")
                return None
        return self._client

    @property
    def db(self):
        if self._db is None and self.client:
            self._db = self.client["IA"]
        return self._db

    def get_users_collection(self):
        if self.db is not None:
            return self.db["users"]
        return None

    def get_dashboard_collection(self):
        if self.db is not None:
            return self.db["dashboard_data"]
        return None


# Global database manager instance
db_manager = DatabaseManager()


def hash_password(password, salt=None):
    """Hash a password with salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(16)

    # Combine password and salt
    salted_password = password + salt
    hashed = hashlib.sha256(salted_password.encode()).hexdigest()

    return hashed, salt


def verify_password(password, stored_hash, salt):
    """Verify a password against stored hash and salt"""
    hashed, _ = hash_password(password, salt)
    return hashed == stored_hash


def verify_user(username, password):
    """Verify user credentials"""
    try:
        users = db_manager.get_users_collection()
        if users is None:
            return False

        user = users.find_one({"username": username})
        if user:
            return verify_password(password, user["password"], user.get("salt", ""))
        return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False


def user_exists(username):
    """Check if username already exists"""
    try:
        users = db_manager.get_users_collection()
        if users is None:
            return True  # Fail safe - assume exists if can't check

        return users.find_one({"username": username}) is not None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return True  # Fail safe


def validate_password_strength(password):
    """Validate password meets security requirements"""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    return errors


def validate_email(email):
    """Basic email validation"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def register_user(username, password, email):
    """Register a new user with enhanced validation"""
    try:
        users = db_manager.get_users_collection()
        if users is None:
            return False, "Database connection error"

        # Validate inputs
        if not username or not password or not email:
            return False, "All fields are required"

        if len(username) < 3:
            return False, "Username must be at least 3 characters long"

        if user_exists(username):
            return False, "Username already exists"

        if not validate_email(email):
            return False, "Please enter a valid email address"

        # Check if email already exists
        if users.find_one({"email": email}):
            return False, "Email already registered"

        # Validate password strength
        password_errors = validate_password_strength(password)
        if password_errors:
            return False, "; ".join(password_errors)

        # Hash password with salt
        hashed_password, salt = hash_password(password)

        # Create user document
        user_doc = {
            "username": username,
            "password": hashed_password,
            "salt": salt,
            "email": email.lower(),
            "role": "user",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "failed_login_attempts": 0,
            "account_locked_until": None,
        }

        users.insert_one(user_doc)
        return True, "Registration successful"

    except DuplicateKeyError:
        return False, "Username or email already exists"
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False, "Registration failed. Please try again."


def update_last_login(username):
    """Update user's last login timestamp"""
    try:
        users = db_manager.get_users_collection()
        if users:
            users.update_one(
                {"username": username},
                {
                    "$set": {"last_login": datetime.utcnow()},
                    "$unset": {"failed_login_attempts": "", "account_locked_until": ""},
                },
            )
    except Exception as e:
        st.error(f"Error updating login time: {str(e)}")


def handle_failed_login(username):
    """Handle failed login attempts and account locking"""
    try:
        users = db_manager.get_users_collection()
        if users:
            user = users.find_one({"username": username})
            if user:
                failed_attempts = user.get("failed_login_attempts", 0) + 1
                update_data = {"failed_login_attempts": failed_attempts}

                # Lock account after 5 failed attempts for 15 minutes
                if failed_attempts >= 5:
                    update_data["account_locked_until"] = datetime.utcnow() + timedelta(
                        minutes=15
                    )

                users.update_one({"username": username}, {"$set": update_data})
    except Exception as e:
        st.error(f"Error handling failed login: {str(e)}")


def is_account_locked(username):
    """Check if account is locked due to failed login attempts"""
    try:
        users = db_manager.get_users_collection()
        if users:
            user = users.find_one({"username": username})
            if user and user.get("account_locked_until"):
                if datetime.utcnow() < user["account_locked_until"]:
                    return True, user["account_locked_until"]
                else:
                    # Unlock account
                    users.update_one(
                        {"username": username},
                        {
                            "$unset": {
                                "account_locked_until": "",
                                "failed_login_attempts": "",
                            }
                        },
                    )
        return False, None
    except Exception as e:
        st.error(f"Error checking account lock: {str(e)}")
        return False, None


def get_user_info(username):
    """Get user information (excluding sensitive data)"""
    try:
        users = db_manager.get_users_collection()
        if users:
            user = users.find_one({"username": username})
            if user:
                # Remove sensitive information
                safe_user_info = {
                    "username": user["username"],
                    "email": user["email"],
                    "role": user.get("role", "user"),
                    "created_at": user.get("created_at"),
                    "last_login": user.get("last_login"),
                    "is_active": user.get("is_active", True),
                }
                return safe_user_info
        return None
    except Exception as e:
        st.error(f"Error retrieving user info: {str(e)}")
        return None


def change_password(username, old_password, new_password):
    """Change user password"""
    try:
        if not verify_user(username, old_password):
            return False, "Current password is incorrect"

        password_errors = validate_password_strength(new_password)
        if password_errors:
            return False, "; ".join(password_errors)

        hashed_password, salt = hash_password(new_password)

        users = db_manager.get_users_collection()
        if users:
            users.update_one(
                {"username": username},
                {"$set": {"password": hashed_password, "salt": salt}},
            )
            return True, "Password changed successfully"

        return False, "Database error"
    except Exception as e:
        st.error(f"Error changing password: {str(e)}")
        return False, "Password change failed"
