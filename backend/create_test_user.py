"""
Create a test user in the local MongoDB database.
This script is useful for testing the login functionality.
"""
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import os

# Set environment variable to use local MongoDB
os.environ['MONGODB_CONNECTION_TYPE'] = 'local'

# Import configuration after setting environment variable
from config import MongoDBConfig

def create_test_user():
    """Create a test user in the local MongoDB database."""
    print("Creating test user in local MongoDB database...")
    
    # Connect to local MongoDB
    client = MongoClient(MongoDBConfig.LOCAL_URI)
    db = client[MongoDBConfig.LOCAL_DB_NAME]
    
    # Check if users collection exists
    if 'users' not in db.list_collection_names():
        print("Creating users collection...")
        users = db.create_collection('users')
        # Create indexes for better performance
        users.create_index([('username', 1)], unique=True)
        users.create_index([('email', 1)], unique=True)
        print("Created users collection with indexes")
    
    # Get users collection
    users_collection = db['users']
    
    # Check if test user already exists
    existing_user = users_collection.find_one({'username': 'testuser'})
    if existing_user:
        print("Test user already exists. Skipping creation.")
        return
    
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
    
    # Insert test user
    result = users_collection.insert_one(test_user)
    print(f"Created test user with ID: {result.inserted_id}")
    
    # Insert test admin
    result = users_collection.insert_one(test_admin)
    print(f"Created test admin with ID: {result.inserted_id}")
    
    print("Test users created successfully")
    print("You can now log in with:")
    print("Username: testuser")
    print("Password: password123")
    print("Or as admin:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    create_test_user()
