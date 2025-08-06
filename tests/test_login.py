import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from login import (
    hash_password, verify_password, verify_user, user_exists,
    validate_password_strength, validate_email, register_user,
    update_last_login, handle_failed_login, is_account_locked,
    get_user_info, change_password, DatabaseManager
)


class TestPasswordFunctions(unittest.TestCase):
    """Test cases for password hashing and verification functions"""

    def test_hash_password_with_salt(self):
        """Test password hashing with provided salt"""
        password = "testpassword123"
        salt = "testsalt"
        
        hashed, returned_salt = hash_password(password, salt)
        
        self.assertEqual(returned_salt, salt)
        self.assertIsInstance(hashed, str)
        self.assertEqual(len(hashed), 64)  # SHA256 hex length

    def test_hash_password_without_salt(self):
        """Test password hashing without provided salt (generates new salt)"""
        password = "testpassword123"
        
        hashed, salt = hash_password(password)
        
        self.assertIsInstance(hashed, str)
        self.assertIsInstance(salt, str)
        self.assertEqual(len(hashed), 64)  # SHA256 hex length
        self.assertEqual(len(salt), 32)  # 16 bytes -> 32 hex chars

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed, salt = hash_password(password)
        
        result = verify_password(password, hashed, salt)
        
        self.assertTrue(result)

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed, salt = hash_password(password)
        
        result = verify_password(wrong_password, hashed, salt)
        
        self.assertFalse(result)


class TestPasswordValidation(unittest.TestCase):
    """Test cases for password validation functions"""

    def test_validate_password_strength_strong(self):
        """Test password strength validation with strong password"""
        strong_password = "StrongPass123!"
        
        errors = validate_password_strength(strong_password)
        
        self.assertEqual(len(errors), 0)

    def test_validate_password_strength_weak(self):
        """Test password strength validation with weak password"""
        weak_password = "weak"
        
        errors = validate_password_strength(weak_password)
        
        self.assertGreater(len(errors), 0)
        self.assertIn("Password must be at least 8 characters long", errors)

    def test_validate_password_missing_uppercase(self):
        """Test password validation missing uppercase letter"""
        password = "lowercase123!"
        
        errors = validate_password_strength(password)
        
        self.assertIn("Password must contain at least one uppercase letter", errors)

    def test_validate_password_missing_lowercase(self):
        """Test password validation missing lowercase letter"""
        password = "UPPERCASE123!"
        
        errors = validate_password_strength(password)
        
        self.assertIn("Password must contain at least one lowercase letter", errors)

    def test_validate_password_missing_number(self):
        """Test password validation missing number"""
        password = "Password!"
        
        errors = validate_password_strength(password)
        
        self.assertIn("Password must contain at least one number", errors)

    def test_validate_password_missing_special_char(self):
        """Test password validation missing special character"""
        password = "Password123"
        
        errors = validate_password_strength(password)
        
        self.assertIn("Password must contain at least one special character", errors)


class TestEmailValidation(unittest.TestCase):
    """Test cases for email validation"""

    def test_validate_email_valid(self):
        """Test email validation with valid email"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test123@test-domain.org"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(validate_email(email))

    def test_validate_email_invalid(self):
        """Test email validation with invalid email"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "test@",
            "test.domain.com",
            ""
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(validate_email(email))


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_manager = DatabaseManager()

    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://test:test@localhost:27017/test'})
    @patch('pymongo.MongoClient')
    def test_client_property_success(self, mock_mongo_client):
        """Test successful client connection"""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        client = self.db_manager.client
        
        self.assertEqual(client, mock_client)
        mock_client.server_info.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch('streamlit.error')
    def test_client_property_no_uri(self, mock_st_error):
        """Test client property with no MongoDB URI"""
        client = self.db_manager.client
        
        self.assertIsNone(client)
        mock_st_error.assert_called_once()

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_db_property(self, mock_mongo_client):
        """Test database property"""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        
        db = self.db_manager.db
        
        self.assertEqual(db, mock_db)
        mock_client.__getitem__.assert_called_with("IA")


class TestUserFunctions(unittest.TestCase):
    """Test cases for user-related functions"""

    @patch('login.db_manager')
    def test_verify_user_success(self, mock_db_manager):
        """Test successful user verification"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        
        # Mock user data
        mock_user = {
            "username": "testuser",
            "password": "hashed_password",
            "salt": "testsalt"
        }
        mock_collection.find_one.return_value = mock_user
        
        with patch('login.verify_password', return_value=True):
            result = verify_user("testuser", "password")
        
        self.assertTrue(result)

    @patch('login.db_manager')
    def test_verify_user_not_found(self, mock_db_manager):
        """Test user verification with non-existent user"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_collection.find_one.return_value = None
        
        result = verify_user("nonexistent", "password")
        
        self.assertFalse(result)

    @patch('login.db_manager')
    def test_user_exists_true(self, mock_db_manager):
        """Test user_exists function when user exists"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {"username": "testuser"}
        
        result = user_exists("testuser")
        
        self.assertTrue(result)

    @patch('login.db_manager')
    def test_user_exists_false(self, mock_db_manager):
        """Test user_exists function when user doesn't exist"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_collection.find_one.return_value = None
        
        result = user_exists("nonexistent")
        
        self.assertFalse(result)

    @patch('login.db_manager')
    def test_register_user_success(self, mock_db_manager):
        """Test successful user registration"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_collection.find_one.return_value = None  # User doesn't exist
        
        with patch('login.user_exists', return_value=False):
            success, message = register_user("newuser", "StrongPass123!", "test@example.com")
        
        self.assertTrue(success)
        self.assertEqual(message, "Registration successful")
        mock_collection.insert_one.assert_called_once()

    @patch('login.db_manager')
    def test_register_user_existing_username(self, mock_db_manager):
        """Test user registration with existing username"""
        with patch('login.user_exists', return_value=True):
            success, message = register_user("existinguser", "StrongPass123!", "test@example.com")
        
        self.assertFalse(success)
        self.assertEqual(message, "Username already exists")

    def test_register_user_weak_password(self):
        """Test user registration with weak password"""
        with patch('login.user_exists', return_value=False):
            success, message = register_user("newuser", "weak", "test@example.com")
        
        self.assertFalse(success)
        self.assertIn("Password must be", message)

    def test_register_user_invalid_email(self):
        """Test user registration with invalid email"""
        with patch('login.user_exists', return_value=False):
            success, message = register_user("newuser", "StrongPass123!", "invalid-email")
        
        self.assertFalse(success)
        self.assertEqual(message, "Please enter a valid email address")

    @patch('login.db_manager')
    def test_update_last_login(self, mock_db_manager):
        """Test updating last login timestamp"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        
        update_last_login("testuser")
        
        mock_collection.update_one.assert_called_once()

    @patch('login.db_manager')
    def test_handle_failed_login(self, mock_db_manager):
        """Test handling failed login attempts"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {"failed_login_attempts": 3}
        
        handle_failed_login("testuser")
        
        mock_collection.update_one.assert_called_once()

    @patch('login.db_manager')
    def test_is_account_locked_true(self, mock_db_manager):
        """Test account lock check when account is locked"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        future_time = datetime.utcnow() + timedelta(minutes=10)
        mock_collection.find_one.return_value = {
            "account_locked_until": future_time
        }
        
        locked, unlock_time = is_account_locked("testuser")
        
        self.assertTrue(locked)
        self.assertEqual(unlock_time, future_time)

    @patch('login.db_manager')
    def test_is_account_locked_false(self, mock_db_manager):
        """Test account lock check when account is not locked"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {"username": "testuser"}
        
        locked, unlock_time = is_account_locked("testuser")
        
        self.assertFalse(locked)
        self.assertIsNone(unlock_time)

    @patch('login.db_manager')
    def test_get_user_info(self, mock_db_manager):
        """Test getting user information"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "hashed_password",  # Should be excluded
            "salt": "salt",  # Should be excluded
            "role": "user",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        mock_collection.find_one.return_value = mock_user
        
        user_info = get_user_info("testuser")
        
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["username"], "testuser")
        self.assertEqual(user_info["email"], "test@example.com")
        self.assertNotIn("password", user_info)
        self.assertNotIn("salt", user_info)

    @patch('login.db_manager')
    def test_change_password_success(self, mock_db_manager):
        """Test successful password change"""
        mock_collection = MagicMock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        
        with patch('login.verify_user', return_value=True):
            success, message = change_password("testuser", "oldpass", "NewStrongPass123!")
        
        self.assertTrue(success)
        self.assertEqual(message, "Password changed successfully")
        mock_collection.update_one.assert_called_once()

    def test_change_password_wrong_current(self):
        """Test password change with wrong current password"""
        with patch('login.verify_user', return_value=False):
            success, message = change_password("testuser", "wrongpass", "NewStrongPass123!")
        
        self.assertFalse(success)
        self.assertEqual(message, "Current password is incorrect")

    def test_change_password_weak_new(self):
        """Test password change with weak new password"""
        with patch('login.verify_user', return_value=True):
            success, message = change_password("testuser", "oldpass", "weak")
        
        self.assertFalse(success)
        self.assertIn("Password must be", message)


if __name__ == '__main__':
    unittest.main()