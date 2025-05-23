"""
Configuration settings for the application.
This file contains environment-specific settings.
"""
import os

# MongoDB Configuration
class MongoDBConfig:
    # Default to local MongoDB for development
    LOCAL_URI = 'mongodb://localhost:27017/'
    LOCAL_DB_NAME = 'Newpy'

    # MongoDB Atlas configuration (if available)
    ATLAS_URI = 'mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
    ATLAS_DB_NAME = 'Newpy'

    # Direct connection string with explicit hosts
    # Note: This is a placeholder. If direct connection is needed, update with the correct server addresses from the new cluster
    DIRECT_URI = 'mongodb://kavin88701:mGmvb7QugKUb0O7z@ac-zm7hkzz-shard-00-00.zik7il3.mongodb.net:27017,ac-zm7hkzz-shard-00-01.zik7il3.mongodb.net:27017,ac-zm7hkzz-shard-00-02.zik7il3.mongodb.net:27017/?ssl=true&replicaSet=atlas-ixvlxl-shard-0&authSource=admin&retryWrites=true&w=majority'

    # Use environment variable to determine which connection to use
    # Options: 'local', 'atlas', 'direct'
    CONNECTION_TYPE = os.environ.get('MONGODB_CONNECTION_TYPE', 'local')

    # Test database name for unit tests
    TEST_DB_NAME = 'test_db'

    @classmethod
    def get_connection_uri(cls):
        """Get the appropriate MongoDB connection URI based on configuration."""
        if cls.CONNECTION_TYPE == 'atlas':
            return cls.ATLAS_URI
        elif cls.CONNECTION_TYPE == 'direct':
            return cls.DIRECT_URI
        else:
            return cls.LOCAL_URI

    @classmethod
    def get_db_name(cls):
        """Get the appropriate database name."""
        if os.environ.get('TESTING') == '1':
            return cls.TEST_DB_NAME

        if cls.CONNECTION_TYPE == 'local':
            return cls.LOCAL_DB_NAME
        else:
            return cls.ATLAS_DB_NAME

# JWT Configuration
class JWTConfig:
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')  # Change this in production
    ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours in seconds

# File Upload Configuration
class FileUploadConfig:
    # Use an absolute path for the upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size

# CORS Configuration
class CORSConfig:
    ALLOWED_ORIGINS = [
        "http://localhost:3000",  # React frontend
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # React frontend on port 3001
        "http://127.0.0.1:3001"
    ]
