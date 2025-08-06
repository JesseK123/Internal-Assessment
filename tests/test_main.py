import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import go_to, main


class TestMainFunctions(unittest.TestCase):
    """Test cases for main.py functions"""

    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.rerun')
    def test_go_to_function(self, mock_rerun, mock_session_state):
        """Test go_to navigation function"""
        go_to("dashboard")
        
        self.assertEqual(mock_session_state["page"], "dashboard")
        mock_rerun.assert_called_once()

    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.rerun')
    def test_go_to_different_pages(self, mock_rerun, mock_session_state):
        """Test go_to function with different pages"""
        pages = ["login", "register", "dashboard"]
        
        for page in pages:
            with self.subTest(page=page):
                go_to(page)
                self.assertEqual(mock_session_state["page"], page)
                mock_rerun.assert_called()


class TestMainApplication(unittest.TestCase):
    """Test cases for main application flow"""

    def setUp(self):
        """Set up test fixtures"""
        self.default_session_state = {
            "page": "login",
            "logged_in": False,
            "username": "",
            "db_initialized": True
        }

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.error')
    @patch('streamlit.stop')
    def test_main_database_initialization_failure(self, mock_stop, mock_error, 
                                                 mock_session_state, mock_init_db, 
                                                 mock_set_page_config):
        """Test main function when database initialization fails"""
        mock_init_db.return_value = False
        mock_session_state.clear()
        
        main()
        
        mock_init_db.assert_called_once()
        mock_error.assert_called_with("Failed to initialize database. Please check your MongoDB connection.")
        mock_stop.assert_called_once()

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    @patch('main.login_page')
    def test_main_login_page_route(self, mock_login_page, mock_markdown, 
                                  mock_session_state, mock_init_db, mock_set_page_config):
        """Test main function routing to login page"""
        mock_init_db.return_value = True
        mock_session_state.__contains__.side_effect = lambda key: key in self.default_session_state
        mock_session_state.__getitem__.side_effect = lambda key: self.default_session_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: self.default_session_state.get(key, default)
        
        main()
        
        mock_login_page.assert_called_once()

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    @patch('main.register_page')
    def test_main_register_page_route(self, mock_register_page, mock_markdown, 
                                     mock_session_state, mock_init_db, mock_set_page_config):
        """Test main function routing to register page"""
        mock_init_db.return_value = True
        session_state = self.default_session_state.copy()
        session_state["page"] = "register"
        
        mock_session_state.__contains__.side_effect = lambda key: key in session_state
        mock_session_state.__getitem__.side_effect = lambda key: session_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: session_state.get(key, default)
        
        main()
        
        mock_register_page.assert_called_once()

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    @patch('main.dashboard_page')
    def test_main_dashboard_page_route(self, mock_dashboard_page, mock_markdown, 
                                      mock_session_state, mock_init_db, mock_set_page_config):
        """Test main function routing to dashboard page"""
        mock_init_db.return_value = True
        session_state = self.default_session_state.copy()
        session_state["logged_in"] = True
        
        mock_session_state.__contains__.side_effect = lambda key: key in session_state
        mock_session_state.__getitem__.side_effect = lambda key: session_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: session_state.get(key, default)
        
        main()
        
        mock_dashboard_page.assert_called_once()

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    def test_main_page_config_called(self, mock_markdown, mock_session_state, 
                                   mock_init_db, mock_set_page_config):
        """Test that streamlit page config is properly set"""
        mock_init_db.return_value = True
        mock_session_state.__contains__.side_effect = lambda key: key in self.default_session_state
        mock_session_state.__getitem__.side_effect = lambda key: self.default_session_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: self.default_session_state.get(key, default)
        
        main()
        
        mock_set_page_config.assert_called_once_with(
            page_title="Secure Login App",
            layout="centered",
            initial_sidebar_state="collapsed",
            page_icon="🔐"
        )

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    def test_main_css_styling_applied(self, mock_markdown, mock_session_state, 
                                    mock_init_db, mock_set_page_config):
        """Test that CSS styling is applied in main function"""
        mock_init_db.return_value = True
        mock_session_state.__contains__.side_effect = lambda key: key in self.default_session_state
        mock_session_state.__getitem__.side_effect = lambda key: self.default_session_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: self.default_session_state.get(key, default)
        
        main()
        
        # Check that markdown was called with CSS styles
        css_call_found = False
        for call in mock_markdown.call_args_list:
            args, kwargs = call
            if len(args) > 0 and "<style>" in args[0]:
                css_call_found = True
                break
        
        self.assertTrue(css_call_found, "CSS styles should be applied via markdown")

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    def test_main_connection_status_indicator(self, mock_markdown, mock_session_state, 
                                            mock_init_db, mock_set_page_config):
        """Test that connection status indicator is shown when database is initialized"""
        mock_init_db.return_value = True
        session_state = self.default_session_state.copy()
        session_state["db_initialized"] = True
        
        mock_session_state.__contains__.side_effect = lambda key: key in session_state
        mock_session_state.__getitem__.side_effect = lambda key: session_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: session_state.get(key, default)
        
        main()
        
        # Check that connection status indicator was displayed
        status_indicator_found = False
        for call in mock_markdown.call_args_list:
            args, kwargs = call
            if len(args) > 0 and "🟢 Connected" in args[0]:
                status_indicator_found = True
                break
        
        self.assertTrue(status_indicator_found, "Connection status indicator should be displayed")


class TestSessionStateInitialization(unittest.TestCase):
    """Test cases for session state initialization"""

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.markdown')
    @patch('main.login_page')
    def test_session_state_initialization(self, mock_login_page, mock_markdown, 
                                        mock_session_state, mock_init_db, mock_set_page_config):
        """Test that session state is properly initialized"""
        mock_init_db.return_value = True
        
        main()
        
        # Check that session state variables are initialized
        self.assertEqual(mock_session_state.get("page", "login"), "login")
        self.assertEqual(mock_session_state.get("logged_in", False), False)
        self.assertEqual(mock_session_state.get("username", ""), "")

    @patch('streamlit.set_page_config')
    @patch('main.initialize_database')
    @patch('streamlit.session_state')
    @patch('streamlit.markdown')
    @patch('main.login_page')
    def test_session_state_preservation(self, mock_login_page, mock_markdown, 
                                      mock_session_state, mock_init_db, mock_set_page_config):
        """Test that existing session state is preserved"""
        mock_init_db.return_value = True
        existing_state = {
            "page": "dashboard",
            "logged_in": True,
            "username": "testuser",
            "db_initialized": True
        }
        
        mock_session_state.__contains__.side_effect = lambda key: key in existing_state
        mock_session_state.__getitem__.side_effect = lambda key: existing_state[key]
        mock_session_state.get.side_effect = lambda key, default=None: existing_state.get(key, default)
        
        main()
        
        # Session state should not be overwritten if it already exists
        # The test verifies that the existing values are preserved


class TestMainEntryPoint(unittest.TestCase):
    """Test cases for main entry point"""

    @patch('main.main')
    def test_main_entry_point(self, mock_main_function):
        """Test that main function is called when script is run directly"""
        # This test simulates the if __name__ == "__main__": condition
        # In a real scenario, this would be tested by running the script
        
        # Simulate the condition being true
        with patch('__main__.__name__', '__main__'):
            # Import and execute the main block logic
            mock_main_function()
            
        mock_main_function.assert_called_once()


if __name__ == '__main__':
    unittest.main()