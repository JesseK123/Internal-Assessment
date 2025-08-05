"""
Test configuration file for pytest
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_streamlit():
    """Mock streamlit components for testing"""
    with patch.dict('sys.modules', {
        'streamlit': Mock(),
    }):
        import streamlit as st
        
        # Mock common streamlit functions
        st.title = Mock()
        st.text_input = Mock()
        st.button = Mock()
        st.columns = Mock(return_value=[Mock(), Mock()])
        st.error = Mock()
        st.success = Mock()
        st.warning = Mock()
        st.info = Mock()
        st.markdown = Mock()
        st.write = Mock()
        st.subheader = Mock()
        st.metric = Mock()
        st.tabs = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        st.progress = Mock()
        st.caption = Mock()
        st.divider = Mock()
        st.expander = Mock()
        st.selectbox = Mock()
        st.checkbox = Mock()
        st.form = Mock()
        st.form_submit_button = Mock()
        st.container = Mock()
        st.balloons = Mock()
        st.rerun = Mock()
        st.stop = Mock()
        st.set_page_config = Mock()
        
        # Mock session state
        st.session_state = {}
        
        yield st


@pytest.fixture
def mock_database_manager():
    """Mock database manager for testing"""
    with patch('login.db_manager') as mock_db_manager:
        mock_collection = Mock()
        mock_db_manager.get_users_collection.return_value = mock_collection
        mock_db_manager.get_dashboard_collection.return_value = mock_collection
        yield mock_db_manager, mock_collection


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    from datetime import datetime
    return {
        "username": "testuser",
        "password": "hashed_password_here",
        "salt": "random_salt_here",
        "email": "test@example.com",
        "role": "user",
        "created_at": datetime(2023, 1, 1),
        "last_login": datetime(2023, 12, 1),
        "is_active": True,
        "failed_login_attempts": 0,
        "account_locked_until": None
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing"""
    env_vars = {
        'MONGODB_URI': 'mongodb://test:test@localhost:27017/test_db',
        'DATABASE_NAME': 'test_db',
        'SECRET_KEY': 'test-secret-key',
        'SALT_ROUNDS': '12'
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        yield env_vars


@pytest.fixture
def mock_pymongo():
    """Mock pymongo for database testing"""
    with patch('pymongo.MongoClient') as mock_client:
        mock_database = Mock()
        mock_collection = Mock()
        
        mock_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_database
        mock_database.__getitem__.return_value = mock_collection
        mock_client.server_info = Mock()
        mock_client.admin.command = Mock()
        mock_client.close = Mock()
        
        yield mock_client, mock_database, mock_collection


@pytest.fixture(autouse=True)
def clean_imports():
    """Clean imports before each test to avoid module caching issues"""
    modules_to_remove = []
    for module_name in sys.modules:
        if module_name.startswith(('src.', 'database', 'login', 'ui', 'main')):
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    yield
    
    # Clean up after test
    for module_name in modules_to_remove:
        if module_name in sys.modules:
            del sys.modules[module_name]


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "database: mark test as requiring database")