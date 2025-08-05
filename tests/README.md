# Test Suite for Secure Login Application

This directory contains comprehensive test cases for the authentication application.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_database.py           # Database module tests
├── test_login.py              # Authentication logic tests
├── test_ui.py                 # User interface tests
├── test_main.py               # Main application tests
└── README.md                  # This file
```

## Test Coverage

### 1. Database Module (`test_database.py`)
- **DatabaseConfig class tests:**
  - Connection string management
  - Database connection/disconnection
  - Health checks
  - Index creation
  - Error handling

- **Global functions tests:**
  - Database instance retrieval
  - Collection access
  - Database initialization

### 2. Login Module (`test_login.py`)
- **Password functions:**
  - Password hashing with/without salt
  - Password verification
  - Password strength validation

- **User management:**
  - User registration with validation
  - User authentication
  - Account locking mechanisms
  - Login attempt tracking
  - Password change functionality

- **Email validation:**
  - Valid/invalid email format testing

### 3. UI Module (`test_ui.py`)
- **Password strength calculator:**
  - Different strength levels
  - Character variety scoring
  - Length-based scoring

- **Page functions:**
  - Login page behavior
  - Registration page functionality
  - Dashboard display
  - Navigation testing

### 4. Main Module (`test_main.py`)
- **Application routing:**
  - Page navigation
  - Session state management
  - Database initialization handling

- **Configuration:**
  - Streamlit page setup
  - CSS styling application
  - Connection status indicators

## Running Tests

### Prerequisites
Install test dependencies:
```bash
pip install pytest pytest-mock
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Files
```bash
pytest tests/test_database.py
pytest tests/test_login.py
pytest tests/test_ui.py
pytest tests/test_main.py
```

### Run Tests with Coverage
```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

### Run Tests by Markers
```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m database      # Run only database tests
pytest -m slow          # Run only slow tests
```

## Test Categories

### Unit Tests
- Test individual functions and methods in isolation
- Use mocks to isolate dependencies
- Fast execution
- Most of the tests in this suite are unit tests

### Integration Tests
- Test interactions between components
- May require database connections
- Slower execution
- Marked with `@pytest.mark.integration`

### Mock Usage
The tests extensively use mocking to:
- Isolate units under test
- Simulate database responses
- Mock Streamlit components
- Control external dependencies

## Test Fixtures

### Available Fixtures (in `conftest.py`)
- `mock_streamlit`: Mocks all Streamlit components
- `mock_database_manager`: Mocks database manager and collections
- `sample_user_data`: Provides sample user data for testing
- `mock_environment_variables`: Sets up test environment variables
- `mock_pymongo`: Mocks PyMongo client and database operations

## Common Test Patterns

### Testing Database Operations
```python
@patch('login.db_manager')
def test_user_function(self, mock_db_manager):
    mock_collection = MagicMock()
    mock_db_manager.get_users_collection.return_value = mock_collection
    
    # Test your function
    result = your_function()
    
    # Assert expectations
    mock_collection.find_one.assert_called_once()
```

### Testing Streamlit UI
```python
@patch('streamlit.button')
@patch('streamlit.text_input')
def test_ui_component(self, mock_text_input, mock_button):
    mock_text_input.side_effect = ["username", "password"]
    mock_button.return_value = True
    
    # Test your UI function
    ui_function()
    
    # Assert UI interactions
    mock_button.assert_called()
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Mocking**: Use mocks to isolate the code under test from external dependencies
3. **Clear Names**: Test names should clearly describe what is being tested
4. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
5. **Edge Cases**: Test both happy path and error conditions

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure the `src` directory is in the Python path
2. **Mock Issues**: Ensure mocks are patched at the correct location
3. **Streamlit Warnings**: Some Streamlit warnings are normal and filtered out

### Running Individual Tests
```bash
pytest tests/test_database.py::TestDatabaseConfig::test_connection_string_with_env_var
```

### Debugging Tests
```bash
pytest -s -vv tests/test_login.py  # Show print statements and verbose output
```

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add appropriate docstrings
3. Use the existing fixtures where possible
4. Add new markers if needed
5. Update this README if adding new test categories