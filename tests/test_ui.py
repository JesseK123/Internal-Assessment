import unittest
from unittest.mock import patch, MagicMock, Mock, call
import sys
import os
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui import calculate_password_strength


class TestPasswordStrength(unittest.TestCase):
    """Test cases for password strength calculation"""

    def test_calculate_password_strength_empty(self):
        """Test password strength calculation with empty password"""
        result = calculate_password_strength("")
        self.assertEqual(result, 0)

    def test_calculate_password_strength_very_weak(self):
        """Test password strength calculation with very weak password"""
        result = calculate_password_strength("abc")
        self.assertLess(result, 30)

    def test_calculate_password_strength_weak(self):
        """Test password strength calculation with weak password"""
        result = calculate_password_strength("password")
        self.assertGreaterEqual(result, 30)
        self.assertLess(result, 60)

    def test_calculate_password_strength_medium(self):
        """Test password strength calculation with medium password"""
        result = calculate_password_strength("Password123")
        self.assertGreaterEqual(result, 60)
        self.assertLess(result, 90)

    def test_calculate_password_strength_strong(self):
        """Test password strength calculation with strong password"""
        result = calculate_password_strength("StrongPass123!")
        self.assertEqual(result, 100)

    def test_calculate_password_strength_length_scoring(self):
        """Test password strength length-based scoring"""
        # Test different length thresholds
        short_pass = calculate_password_strength("Ab1!")  # 4 chars
        medium_pass = calculate_password_strength("AbCd1!")  # 6 chars
        long_pass = calculate_password_strength("AbCdEf1!")  # 8 chars
        
        self.assertLess(short_pass, medium_pass)
        self.assertLess(medium_pass, long_pass)

    def test_calculate_password_strength_character_variety(self):
        """Test password strength character variety scoring"""
        # Test individual character types
        only_lower = calculate_password_strength("abcdefgh")
        with_upper = calculate_password_strength("Abcdefgh")
        with_digit = calculate_password_strength("Abcdefg1")
        with_special = calculate_password_strength("Abcdefg1!")
        
        self.assertLess(only_lower, with_upper)
        self.assertLess(with_upper, with_digit)
        self.assertLess(with_digit, with_special)


class TestUIFunctions(unittest.TestCase):
    """Test cases for UI page functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_go_to = Mock()
        self.mock_verify_user = Mock()
        self.mock_register_user = Mock()
        self.mock_get_user_info = Mock()
        self.mock_change_password = Mock()
        self.mock_is_account_locked = Mock()
        self.mock_handle_failed_login = Mock()
        self.mock_update_last_login = Mock()

    @patch('streamlit.title')
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.error')
    @patch('streamlit.success')
    def test_login_page_empty_credentials(self, mock_success, mock_error, 
                                        mock_columns, mock_button, mock_text_input, mock_title):
        """Test login page with empty credentials"""
        from ui import login_page
        
        # Mock streamlit components
        mock_text_input.side_effect = ["", ""]  # Empty username and password
        mock_button.return_value = True  # Login button clicked
        mock_columns.return_value = [Mock(), Mock()]
        
        login_page(self.mock_go_to, self.mock_verify_user, 
                  self.mock_is_account_locked, self.mock_handle_failed_login, 
                  self.mock_update_last_login)
        
        mock_error.assert_called_with("Please enter both username and password")

    @patch('streamlit.title')
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.error')
    @patch('streamlit.success')
    @patch('streamlit.session_state', new_callable=lambda: {'logged_in': False, 'username': ''})
    def test_login_page_account_locked(self, mock_success, mock_error, 
                                     mock_columns, mock_button, mock_text_input, mock_title):
        """Test login page with locked account"""
        from ui import login_page
        
        # Mock streamlit components
        mock_text_input.side_effect = ["testuser", "password"]
        mock_button.return_value = True
        mock_columns.return_value = [Mock(), Mock()]
        
        # Mock account locked
        unlock_time = datetime.now()
        self.mock_is_account_locked.return_value = (True, unlock_time)
        
        login_page(self.mock_go_to, self.mock_verify_user, 
                  self.mock_is_account_locked, self.mock_handle_failed_login, 
                  self.mock_update_last_login)
        
        self.mock_is_account_locked.assert_called_with("testuser")
        mock_error.assert_called()

    @patch('streamlit.title')
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.error')
    @patch('streamlit.success')
    @patch('streamlit.session_state', new_callable=lambda: {'logged_in': False, 'username': ''})
    def test_login_page_successful_login(self, mock_success, mock_error, 
                                       mock_columns, mock_button, mock_text_input, mock_title):
        """Test successful login"""
        from ui import login_page
        
        # Mock streamlit components
        mock_text_input.side_effect = ["testuser", "password"]
        mock_button.return_value = True
        mock_columns.return_value = [Mock(), Mock()]
        
        # Mock successful verification
        self.mock_is_account_locked.return_value = (False, None)
        self.mock_verify_user.return_value = True
        
        login_page(self.mock_go_to, self.mock_verify_user, 
                  self.mock_is_account_locked, self.mock_handle_failed_login, 
                  self.mock_update_last_login)
        
        self.mock_verify_user.assert_called_with("testuser", "password")
        self.mock_update_last_login.assert_called_with("testuser")
        mock_success.assert_called_with("Login successful!")

    @patch('streamlit.title')
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.error')
    def test_login_page_failed_login(self, mock_error, mock_columns, 
                                   mock_button, mock_text_input, mock_title):
        """Test failed login attempt"""
        from ui import login_page
        
        # Mock streamlit components
        mock_text_input.side_effect = ["testuser", "wrongpassword"]
        mock_button.return_value = True
        mock_columns.return_value = [Mock(), Mock()]
        
        # Mock failed verification
        self.mock_is_account_locked.return_value = (False, None)
        self.mock_verify_user.return_value = False
        
        login_page(self.mock_go_to, self.mock_verify_user, 
                  self.mock_is_account_locked, self.mock_handle_failed_login, 
                  self.mock_update_last_login)
        
        self.mock_handle_failed_login.assert_called_with("testuser")
        mock_error.assert_called_with("Invalid credentials")

    @patch('streamlit.title')
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.success')
    @patch('streamlit.error')
    @patch('streamlit.balloons')
    def test_register_page_successful_registration(self, mock_balloons, mock_error, 
                                                 mock_success, mock_columns, mock_button, 
                                                 mock_text_input, mock_title):
        """Test successful user registration"""
        from ui import register_page
        
        # Mock streamlit components
        mock_text_input.side_effect = ["newuser", "test@example.com", "StrongPass123!", "StrongPass123!"]
        mock_button.return_value = True
        mock_columns.return_value = [Mock(), Mock()]
        
        # Mock successful registration
        self.mock_register_user.return_value = (True, "Registration successful")
        
        register_page(self.mock_go_to, self.mock_register_user)
        
        self.mock_register_user.assert_called_with("newuser", "StrongPass123!", "test@example.com")
        mock_success.assert_called_with("Registration successful")
        mock_balloons.assert_called_once()

    @patch('streamlit.title')
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.error')
    def test_register_page_failed_registration(self, mock_error, mock_columns, 
                                             mock_button, mock_text_input, mock_title):
        """Test failed user registration"""
        from ui import register_page
        
        # Mock streamlit components
        mock_text_input.side_effect = ["existinguser", "test@example.com", "StrongPass123!", "StrongPass123!"]
        mock_button.return_value = True
        mock_columns.return_value = [Mock(), Mock()]
        
        # Mock failed registration
        self.mock_register_user.return_value = (False, "Username already exists")
        
        register_page(self.mock_go_to, self.mock_register_user)
        
        mock_error.assert_called_with("Username already exists")

    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.tabs')
    @patch('streamlit.subheader')
    @patch('streamlit.write')
    @patch('streamlit.button')
    @patch('streamlit.session_state', new_callable=lambda: {'username': 'testuser'})
    def test_dashboard_page_user_info_display(self, mock_button, mock_write, 
                                            mock_subheader, mock_tabs, mock_metric, 
                                            mock_columns, mock_markdown, mock_title):
        """Test dashboard page user info display"""
        from ui import dashboard_page
        
        # Mock user info
        user_info = {
            'username': 'testuser',
            'email': 'test@example.com',
            'role': 'user',
            'created_at': datetime(2023, 1, 1),
            'last_login': datetime(2023, 12, 1),
            'is_active': True
        }
        self.mock_get_user_info.return_value = user_info
        
        # Mock streamlit components
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_button.return_value = False
        
        dashboard_page(self.mock_go_to, self.mock_get_user_info, self.mock_change_password)
        
        self.mock_get_user_info.assert_called_with('testuser')
        mock_title.assert_called_with("📊 Dashboard")

    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.tabs')
    @patch('streamlit.subheader')
    @patch('streamlit.button')
    @patch('streamlit.success')
    @patch('streamlit.rerun')
    @patch('streamlit.session_state', new_callable=lambda: {'username': 'testuser'})
    def test_dashboard_page_logout(self, mock_rerun, mock_success, mock_button, 
                                 mock_subheader, mock_tabs, mock_metric, 
                                 mock_columns, mock_markdown, mock_title):
        """Test dashboard page logout functionality"""
        from ui import dashboard_page
        
        # Mock user info
        self.mock_get_user_info.return_value = {'username': 'testuser'}
        
        # Mock streamlit components - logout button clicked
        mock_columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_button.side_effect = [False] * 10 + [True]  # Last button (logout) clicked
        
        dashboard_page(self.mock_go_to, self.mock_get_user_info, self.mock_change_password)
        
        mock_success.assert_called_with("Logged out successfully!")


class TestUIIntegration(unittest.TestCase):
    """Integration tests for UI components"""

    @patch('streamlit.progress')
    @patch('streamlit.caption')
    def test_password_strength_indicator_integration(self, mock_caption, mock_progress):
        """Test password strength indicator integration"""
        from ui import calculate_password_strength
        
        # Test different password strengths
        passwords = [
            ("", 0),
            ("weak", 25),
            ("Medium123", 85),
            ("VeryStrong123!", 100)
        ]
        
        for password, expected_min_strength in passwords:
            with self.subTest(password=password):
                strength = calculate_password_strength(password)
                self.assertGreaterEqual(strength, expected_min_strength)


if __name__ == '__main__':
    unittest.main()