"""
MongoDB Atlas connector module.
This module provides functions to connect to MongoDB Atlas and perform database operations.
"""
import os
import ssl
import certifi
import urllib.parse
from pymongo import MongoClient
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# MongoDB Atlas connection string
MONGODB_URI = 'mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
DB_NAME = 'Newpy'

def get_client():
    """
    Get a MongoDB client with various connection options.
    Tries different approaches to connect to MongoDB Atlas.
    """
    # Try different connection approaches
    exceptions = []
    
    # Approach 1: Standard connection
    try:
        print("Trying standard connection...")
        client = MongoClient(MONGODB_URI)
        # Test the connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas with standard connection")
        return client
    except Exception as e:
        exceptions.append(f"Standard connection failed: {str(e)}")
    
    # Approach 2: With SSL CA file
    try:
        print("Trying connection with SSL CA file...")
        client = MongoClient(
            MONGODB_URI,
            tlsCAFile=certifi.where()
        )
        # Test the connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas with SSL CA file")
        return client
    except Exception as e:
        exceptions.append(f"SSL CA file connection failed: {str(e)}")
    
    # Approach 3: With SSL disabled
    try:
        print("Trying connection with SSL verification disabled...")
        client = MongoClient(
            MONGODB_URI,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        # Test the connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas with SSL verification disabled")
        return client
    except Exception as e:
        exceptions.append(f"SSL disabled connection failed: {str(e)}")
    
    # Approach 4: With direct connection
    try:
        print("Trying direct connection...")
        # Parse the SRV URI to get username, password, and host
        parts = MONGODB_URI.split('@')
        auth = parts[0].replace('mongodb+srv://', '')
        username, password = auth.split(':')
        
        # URL decode the username and password
        username = urllib.parse.unquote(username)
        password = urllib.parse.unquote(password)
        
        # Construct direct connection string
        direct_uri = f"mongodb://{username}:{password}@ac-uowy13k-shard-00-00.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-01.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-02.01myarq.mongodb.net:27017/{DB_NAME}?ssl=true&replicaSet=atlas-ixvlnj-shard-0&authSource=admin&retryWrites=true&w=majority"
        
        client = MongoClient(
            direct_uri,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        # Test the connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas with direct connection")
        return client
    except Exception as e:
        exceptions.append(f"Direct connection failed: {str(e)}")
    
    # If all approaches fail, raise an exception with all the errors
    raise Exception(f"All MongoDB Atlas connection approaches failed:\n" + "\n".join(exceptions))

def get_database():
    """Get the MongoDB database."""
    client = get_client()
    return client[DB_NAME]

def initialize_database():
    """Initialize the MongoDB database with collections and indexes."""
    try:
        # Get the database
        db = get_database()
        print(f"Connected to database: {DB_NAME}")
        
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
        
        # Create test users if they don't exist
        create_test_users(db)
        
        # Print all collections
        print(f"Available collections: {db.list_collection_names()}")
        print("MongoDB Atlas database initialization complete")
        
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

def create_test_users(db):
    """Create test users in the database if they don't exist."""
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

if __name__ == "__main__":
    # Initialize the database
    initialize_database()
