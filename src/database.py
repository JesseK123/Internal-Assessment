import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig:
    """Database configuration and connection management"""

    def __init__(self):
        self._client = None
        self._db = None
        self.database_name = os.getenv("DATABASE_NAME", "IA")

    @property
    def connection_string(self):
        """Get MongoDB connection string from environment"""
        # Try different environment variable names
        uri = os.getenv("MONGO_URI")
        
        if not uri:
            st.error(
                "⚠️ MongoDB connection string not found. Please set MONGO_URI environment variable."
            )
            return None

        return uri

    def connect(self):
        """Establish database connection"""
        if self._client is None:
            try:
                uri = self.connection_string
                if not uri:
                    return False

                self._client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    maxPoolSize=10,
                )

                # Test the connection
                self._client.server_info()
                self._db = self._client[self.database_name]

                return True

            except ConnectionFailure as e:
                st.error(f"❌ Failed to connect to MongoDB: {str(e)}")
                self._client = None
                return False
            except Exception as e:
                st.error(f"❌ Database connection error: {str(e)}")
                self._client = None
                return False

        return True

    def disconnect(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    def get_database(self):
        """Get database instance"""
        if self.connect():
            return self._db
        return None

    def get_collection(self, collection_name):
        """Get a specific collection"""
        db = self.get_database()
        if db is not None:
            return db[collection_name]
        return None

    def health_check(self):
        """Check database connection health"""
        try:
            if self._client:
                # Ping the database
                self._client.admin.command("ping")
                return True
        except Exception as e:
            st.error(f"Database health check failed: {str(e)}")
        return False

    def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            db = self.get_database()
            if db is not None:
                # Create indexes for users collection
                users = db["users"]
                users.create_index("username", unique=True)
                users.create_index("email", unique=True)
                users.create_index("created_at")
                users.create_index("last_login")

                # Create indexes for dashboard collection
                dashboard = db["dashboard_data"]
                dashboard.create_index("user_id")
                dashboard.create_index("created_at")
                
                # Create indexes for portfolios collection
                portfolios = db["portfolios"]
                portfolios.create_index("user_id")
                portfolios.create_index("created_at")
                portfolios.create_index("portfolio_name")

                return True
        except Exception as e:
            st.warning(f"Could not create indexes: {str(e)}")
        return False


# Global database configuration instance
db_config = DatabaseConfig()


# Convenience functions for backward compatibility
def get_users_collection():
    """Get users collection"""
    return db_config.get_collection("users")


def get_dashboard_collection():
    """Get dashboard collection"""
    return db_config.get_collection("dashboard_data")


def get_portfolios_collection():
    """Get portfolios collection"""
    return db_config.get_collection("portfolios")


def initialize_database():
    """Initialize database with indexes and basic setup"""
    if db_config.connect():
        db_config.create_indexes()
        return True
    return False
