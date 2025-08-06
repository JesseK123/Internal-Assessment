import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import DatabaseConfig, db_config, get_db, get_users_collection, get_dashboard_collection, initialize_database
from pymongo.errors import ConnectionFailure


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for DatabaseConfig class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_config = DatabaseConfig()

    def tearDown(self):
        """Clean up after each test method."""
        self.db_config.disconnect()

    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://test:test@localhost:27017/test'})
    def test_connection_string_with_env_var(self):
        """Test connection string retrieval with environment variable set"""
        uri = self.db_config.connection_string
        self.assertIsNotNone(uri)
        self.assertEqual(uri, 'mongodb://test:test@localhost:27017/test')

    @patch.dict(os.environ, {}, clear=True)
    @patch('streamlit.error')
    def test_connection_string_without_env_var(self, mock_st_error):
        """Test connection string retrieval without environment variable"""
        uri = self.db_config.connection_string
        self.assertIsNone(uri)
        mock_st_error.assert_called_once()

    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017/test'})
    def test_connection_string_alternative_env_vars(self):
        """Test connection string with alternative environment variable names"""
        uri = self.db_config.connection_string
        self.assertEqual(uri, 'mongodb://localhost:27017/test')

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_successful_connection(self, mock_mongo_client):
        """Test successful database connection"""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        result = self.db_config.connect()
        
        self.assertTrue(result)
        mock_mongo_client.assert_called_once()
        mock_client.server_info.assert_called_once()

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_connection_failure(self, mock_mongo_client):
        """Test database connection failure"""
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        with patch('streamlit.error'):
            result = self.db_config.connect()
        
        self.assertFalse(result)
        self.assertIsNone(self.db_config._client)

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_get_database(self, mock_mongo_client):
        """Test getting database instance"""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        
        db = self.db_config.get_database()
        
        self.assertIsNotNone(db)

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_get_collection(self, mock_mongo_client):
        """Test getting a specific collection"""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        collection = self.db_config.get_collection("test_collection")
        
        self.assertIsNotNone(collection)

    def test_disconnect(self):
        """Test database disconnection"""
        mock_client = MagicMock()
        self.db_config._client = mock_client
        
        self.db_config.disconnect()
        
        mock_client.close.assert_called_once()
        self.assertIsNone(self.db_config._client)
        self.assertIsNone(self.db_config._db)

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_health_check_success(self, mock_mongo_client):
        """Test successful health check"""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        self.db_config._client = mock_client
        
        result = self.db_config.health_check()
        
        self.assertTrue(result)
        mock_client.admin.command.assert_called_once_with("ping")

    def test_health_check_failure(self):
        """Test health check failure"""
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = Exception("Ping failed")
        self.db_config._client = mock_client
        
        with patch('streamlit.error'):
            result = self.db_config.health_check()
        
        self.assertFalse(result)

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_create_indexes_success(self, mock_mongo_client):
        """Test successful index creation"""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_dashboard_collection = MagicMock()
        
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.side_effect = lambda x: {
            "users": mock_users_collection,
            "dashboard_data": mock_dashboard_collection
        }[x]
        
        with patch('streamlit.info'):
            result = self.db_config.create_indexes()
        
        self.assertTrue(result)
        mock_users_collection.create_index.assert_called()
        mock_dashboard_collection.create_index.assert_called()

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    def test_create_indexes_failure(self, mock_mongo_client):
        """Test index creation failure"""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.side_effect = Exception("Index creation failed")
        
        with patch('streamlit.warning'):
            result = self.db_config.create_indexes()
        
        self.assertFalse(result)


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global database functions"""

    @patch('database.db_config')
    def test_get_db(self, mock_db_config):
        """Test get_db function"""
        mock_database = MagicMock()
        mock_db_config.get_database.return_value = mock_database
        
        result = get_db()
        
        self.assertEqual(result, mock_database)
        mock_db_config.get_database.assert_called_once()

    @patch('database.db_config')
    def test_get_users_collection(self, mock_db_config):
        """Test get_users_collection function"""
        mock_collection = MagicMock()
        mock_db_config.get_collection.return_value = mock_collection
        
        result = get_users_collection()
        
        self.assertEqual(result, mock_collection)
        mock_db_config.get_collection.assert_called_once_with("users")

    @patch('database.db_config')
    def test_get_dashboard_collection(self, mock_db_config):
        """Test get_dashboard_collection function"""
        mock_collection = MagicMock()
        mock_db_config.get_collection.return_value = mock_collection
        
        result = get_dashboard_collection()
        
        self.assertEqual(result, mock_collection)
        mock_db_config.get_collection.assert_called_once_with("dashboard_data")

    @patch('database.db_config')
    def test_initialize_database_success(self, mock_db_config):
        """Test successful database initialization"""
        mock_db_config.connect.return_value = True
        mock_db_config.create_indexes.return_value = True
        
        result = initialize_database()
        
        self.assertTrue(result)
        mock_db_config.connect.assert_called_once()
        mock_db_config.create_indexes.assert_called_once()

    @patch('database.db_config')
    def test_initialize_database_failure(self, mock_db_config):
        """Test database initialization failure"""
        mock_db_config.connect.return_value = False
        
        result = initialize_database()
        
        self.assertFalse(result)
        mock_db_config.connect.assert_called_once()
        mock_db_config.create_indexes.assert_not_called()


if __name__ == '__main__':
    unittest.main()