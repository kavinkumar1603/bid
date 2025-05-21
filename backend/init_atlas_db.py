"""
Initialize the MongoDB Atlas database with the necessary collections and indexes.
This script should be run once to set up the MongoDB Atlas database.
"""
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import os
import ssl
import certifi

# Set environment variable to use MongoDB Atlas
os.environ['MONGODB_CONNECTION_TYPE'] = 'atlas'

# Import configuration after setting environment variable
from config import MongoDBConfig

def init_atlas_db():
    """Initialize the MongoDB Atlas database with the necessary collections and indexes."""
    print("Initializing MongoDB Atlas database...")
    print(f"Using connection URI: {MongoDBConfig.ATLAS_URI}")
    
    # Connect to MongoDB Atlas with different SSL configurations
    try:
        # First try with standard SSL settings
        print("Trying connection with standard SSL settings...")
        client = MongoClient(
            MongoDBConfig.ATLAS_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tlsCAFile=certifi.where()
        )
        # Test the connection
        client.admin.command('ping')
        print("Connected to MongoDB Atlas with standard SSL settings")
    except Exception as e1:
        print(f"Standard SSL connection failed: {str(e1)}")
        
        # Second try with more permissive SSL settings
        print("Trying connection with permissive SSL settings...")
        client = MongoClient(
            MongoDBConfig.ATLAS_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tlsAllowInvalidCertificates=True,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        # Test the connection
        client.admin.command('ping')
        print("Connected to MongoDB Atlas with permissive SSL settings")
    
    # Get the database
    db = client[MongoDBConfig.ATLAS_DB_NAME]
    print(f"Using database: {MongoDBConfig.ATLAS_DB_NAME}")
    
    # Create collections if they don't exist
    if 'users' not in db.list_collection_names():
        print("Creating users collection...")
        users = db.create_collection('users')
        # Create indexes for better performance
        users.create_index([('username', 1)], unique=True)
        users.create_index([('email', 1)], unique=True)
        print("Created users collection with indexes")
    
    if 'items' not in db.list_collection_names():
        print("Creating items collection...")
        items = db.create_collection('items')
        # Create indexes for better performance
        items.create_index([('seller_id', 1)])
        items.create_index([('status', 1)])
        print("Created items collection with indexes")
    
    if 'bids' not in db.list_collection_names():
        print("Creating bids collection...")
        bids = db.create_collection('bids')
        # Create indexes for better performance
        bids.create_index([('item_id', 1)])
        bids.create_index([('user_id', 1)])
        print("Created bids collection with indexes")
    
    # Create test users
    users_collection = db['users']
    
    # Check if test user already exists
    existing_user = users_collection.find_one({'username': 'testuser'})
    if existing_user:
        print("Test user already exists. Skipping creation.")
    else:
        # Create test user
        test_user = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': generate_password_hash('password123'),
            'phone_number': '+1234567890',
            'address': '123 Test Street, Test City, Test Country',
            'profile_image': None,
            'user_type': 'user',
            'created_at': datetime.now(timezone.utc)
        }
        
        # Insert test user
        result = users_collection.insert_one(test_user)
        print(f"Created test user with ID: {result.inserted_id}")
    
    # Check if test admin already exists
    existing_admin = users_collection.find_one({'username': 'admin'})
    if existing_admin:
        print("Test admin already exists. Skipping creation.")
    else:
        # Create test admin
        test_admin = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password_hash': generate_password_hash('admin123'),
            'phone_number': '+0987654321',
            'address': '456 Admin Street, Admin City, Admin Country',
            'profile_image': None,
            'user_type': 'admin',
            'created_at': datetime.now(timezone.utc)
        }
        
        # Insert test admin
        result = users_collection.insert_one(test_admin)
        print(f"Created test admin with ID: {result.inserted_id}")
    
    # Print all collections
    print(f"Available collections: {db.list_collection_names()}")
    print("MongoDB Atlas database initialization complete")
    print("You can now log in with:")
    print("Username: testuser")
    print("Password: password123")
    print("Or as admin:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    init_atlas_db()
