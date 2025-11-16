import re
from datetime import datetime, timedelta, timezone
from pymongo.errors import DuplicateKeyError
import streamlit as st
from bson import ObjectId
from database import get_users_collection, get_dashboard_collection, get_portfolios_collection


def get_collection_safely(collection_getter):
    """Safely get a database collection with error handling"""
    collection = collection_getter()
    if collection is None:
        return None, (False, "Database connection failed")
    return collection, None


def verify_user(username, password):
    """Verify user credentials"""
    try:
        users = get_users_collection()
        if users is None:
            return False

        user = users.find_one({"username": username})
        if user:
            return password == user["password"]
        return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False


def user_exists(username):
    """Check if username already exists"""
    try:
        users = get_users_collection()
        if users is None:
            return True  # Fail safe - assume exists if can't check

        return users.find_one({"username": username}) is not None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return True  # Fail safe


def validate_email(email):
    """Basic email validation"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def register_user(username, password, email):
    """Register a new user with enhanced validation"""
    try:
        users = get_users_collection()
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

        # Create user document
        user_doc = {
            "username": username,
            "password": password,
            "email": email.lower(),
            "role": "user",
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "is_active": True,
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
        users = get_users_collection()
        if users is not None:
            users.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.now(timezone.utc)}},
            )
    except Exception as e:
        st.error(f"Error updating login time: {str(e)}")


def get_user_info(username):
    """Get user information (excluding sensitive data)"""
    try:
        users = get_users_collection()
        if users is not None:
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

        users = get_users_collection()
        if users is not None:
            users.update_one(
                {"username": username},
                {"$set": {"password": new_password}},
            )
            return True, "Password changed successfully"

        return False, "Database error"
    except Exception as e:
        st.error(f"Error changing password: {str(e)}")
        return False, "Password change failed"


# Portfolio management functions
def create_portfolio(username, portfolio_data):
    """Create a new portfolio for a user"""
    try:
        portfolios, error = get_collection_safely(get_portfolios_collection)
        if error:
            return error
        
        # Check if portfolio name already exists for this user
        existing = portfolios.find_one({
            "user_id": username,
            "portfolio_name": portfolio_data["name"]
        })
        
        if existing:
            return False, "Portfolio name already exists"
        
        # Create portfolio document
        portfolio_doc = {
            "user_id": username,
            "portfolio_name": portfolio_data["name"],
            "countries": portfolio_data["countries"],
            "stocks": portfolio_data.get("stocks", []),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "total_value": 0,
            "is_active": True
        }
        
        result = portfolios.insert_one(portfolio_doc)
        if result.inserted_id:
            return True, "Portfolio created successfully"
        else:
            return False, "Failed to create portfolio"
            
    except Exception as e:
        return False, f"Error creating portfolio: {str(e)}"


def get_user_portfolios(username):
    """Get all portfolios for a user"""
    try:
        portfolios = get_portfolios_collection()
        if portfolios is None:
            return []

        user_portfolios = list(portfolios.find({
            "user_id": username,
            "is_active": True
        }).sort("created_at", -1))

        return user_portfolios

    except Exception as e:
        st.error(f"Error fetching portfolios: {str(e)}")
        return []


def get_all_portfolios():
    """Get all portfolios from all users for media feed"""
    try:
        portfolios = get_portfolios_collection()
        if portfolios is None:
            return []

        all_portfolios = list(portfolios.find({
            "is_active": True
        }).sort("created_at", -1))

        return all_portfolios

    except Exception as e:
        st.error(f"Error fetching all portfolios: {str(e)}")
        return []


def get_portfolio_by_id(portfolio_id):
    """Get a specific portfolio by its ID"""
    try:
        portfolios = get_portfolios_collection()
        if portfolios is None:
            return None
        
        portfolio = portfolios.find_one({"_id": ObjectId(portfolio_id)})
        return portfolio
        
    except Exception as e:
        st.error(f"Error fetching portfolio: {str(e)}")
        return None


def update_portfolio(portfolio_id, update_data):
    """Update a portfolio"""
    try:
        portfolios, error = get_collection_safely(get_portfolios_collection)
        if error:
            return error
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = portfolios.update_one(
            {"_id": ObjectId(portfolio_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return True, "Portfolio updated successfully"
        else:
            return False, "No changes made to portfolio"
            
    except Exception as e:
        return False, f"Error updating portfolio: {str(e)}"


def delete_portfolio(portfolio_id, username):
    """Delete a portfolio (soft delete by setting is_active to False)"""
    try:
        portfolios, error = get_collection_safely(get_portfolios_collection)
        if error:
            return error
        
        result = portfolios.update_one(
            {"_id": ObjectId(portfolio_id), "user_id": username},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count > 0:
            return True, "Portfolio deleted successfully"
        else:
            return False, "Portfolio not found or already deleted"
            
    except Exception as e:
        return False, f"Error deleting portfolio: {str(e)}"


def add_stock_to_portfolio(portfolio_id, stock_data):
    """Add a stock to a portfolio"""
    try:
        portfolios, error = get_collection_safely(get_portfolios_collection)
        if error:
            return False, error
        
        # Check if stock already exists in portfolio
        portfolio = portfolios.find_one({"_id": ObjectId(portfolio_id)})
        if portfolio:
            existing_stocks = portfolio.get("stocks", [])
            for stock in existing_stocks:
                if stock["symbol"] == stock_data["symbol"]:
                    return False, f"Stock {stock_data['symbol']} already exists in portfolio"
        
        # Add stock to portfolio
        result = portfolios.update_one(
            {"_id": ObjectId(portfolio_id)},
            {
                "$push": {"stocks": stock_data},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        if result.modified_count > 0:
            return True, f"Stock {stock_data['symbol']} added to portfolio"
        else:
            return False, "Failed to add stock to portfolio"
            
    except Exception as e:
        return False, f"Error adding stock: {str(e)}"


def remove_stock_from_portfolio(portfolio_id, stock_symbol):
    """Remove a stock from a portfolio"""
    try:
        portfolios, error = get_collection_safely(get_portfolios_collection)
        if error:
            return error
        
        result = portfolios.update_one(
            {"_id": ObjectId(portfolio_id)},
            {
                "$pull": {"stocks": {"symbol": stock_symbol}},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        if result.modified_count > 0:
            return True, f"Stock {stock_symbol} removed from portfolio"
        else:
            return False, "Stock not found in portfolio"
            
    except Exception as e:
        return False, f"Error removing stock: {str(e)}"
