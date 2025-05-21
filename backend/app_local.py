"""
Modified version of app.py that uses the local MongoDB server.
This is a temporary solution while resolving MongoDB Atlas connection issues.
"""
# Copy of the original app.py with modifications to use local MongoDB

# pylint: disable=unused-argument
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
import json
import re
import ssl
import certifi

# Import configuration
from config import MongoDBConfig, JWTConfig, FileUploadConfig, CORSConfig

app = Flask(__name__)

# Configure CORS more explicitly to handle preflight requests properly
# Note: We're not using the wildcard origin because we need to support credentials
CORS(app, 
     resources={r"/api/*": {"origins": CORSConfig.ALLOWED_ORIGINS}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True,
     max_age=3600,
     vary_header=True)

# MongoDB Configuration - Force local connection
print("Using local MongoDB for this session")
db_name = 'Newpy'
print(f"Using MongoDB database: {db_name}")

# MongoDB connection with proper timeout and retry settings
try:
    print("Attempting to connect to MongoDB...")
    
    # Connect to local MongoDB
    connection_uri = 'mongodb://localhost:27017/'
    print(f"Using connection URI: {connection_uri}")
    
    # Try to connect to MongoDB
    try:
        client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
        
        # Force a connection to verify it works
        client.admin.command('ping')
        db = client.get_database(db_name)
        print(f"Connected to local MongoDB")
        
        # List collections to verify connection
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")
        raise Exception("Local MongoDB connection failed")

    # Initialize collections
    users_collection = db['users']
    items_collection = db['items']
    bids_collection = db['bids']

    # Create indexes for better performance (only if collections don't exist yet)
    if 'users' not in db.list_collection_names():
        users_collection.create_index([('username', 1)], unique=True)
        users_collection.create_index([('email', 1)], unique=True)
        print("Created indexes for users collection")

    # List collections to verify connection
    collections = db.list_collection_names()
    print(f"MongoDB connection successful. Collections: {collections}")

except Exception as e:
    print(f"MongoDB connection error: {str(e)}")
    # Initialize empty collections to prevent app from crashing
    db = None
    users_collection = None
    items_collection = None
    bids_collection = None

    # Create mock collections for testing without MongoDB
    print("Creating mock collections for testing...")

    # Simple mock collection for testing without MongoDB
    class MockCollection:
        def __init__(self, name):
            self.name = name
            self.data = []

        # All methods below intentionally ignore their parameters
        def find_one(self, *args, **kwargs):
            # Simple mock implementation
            return None

        def insert_one(self, *args, **kwargs):
            # Simple mock implementation
            class MockResult:
                def __init__(self):
                    self.inserted_id = "mock_id"
            return MockResult()

        def find(self, *args, **kwargs):
            # Return empty list
            return []

        def create_index(self, *args, **kwargs):
            # Do nothing
            pass

        def aggregate(self, *args, **kwargs):
            # Return empty list
            return []

        def update_one(self, *args, **kwargs):
            # Do nothing
            pass

    # Create mock collections
    users_collection = MockCollection('users')
    items_collection = MockCollection('items')
    bids_collection = MockCollection('bids')

# JWT Configuration
app.config['JWT_SECRET_KEY'] = JWTConfig.SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=JWTConfig.ACCESS_TOKEN_EXPIRES)

# File Upload Configuration
app.config['UPLOAD_FOLDER'] = FileUploadConfig.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = FileUploadConfig.MAX_CONTENT_LENGTH

# Initialize JWT
jwt = JWTManager(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to convert ObjectId to string
def serialize_mongo_id(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Global after_request handler to ensure CORS headers are set on all responses
@app.after_request
def after_request(response):
    # Get the origin from the request
    origin = request.headers.get('Origin')
    
    # If the origin is in our allowed origins, set the CORS headers
    if origin in CORSConfig.ALLOWED_ORIGINS:
        # When using credentials, we must specify the exact origin (not a wildcard)
        response.headers.set('Access-Control-Allow-Origin', origin)
        response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.set('Access-Control-Allow-Credentials', 'true')
        response.headers.set('Vary', 'Origin')  # Important for caching
    elif request.method == 'OPTIONS':
        # For preflight requests, we need to handle origins that might not be in the request
        # Default to the first allowed origin
        response.headers.set('Access-Control-Allow-Origin', CORSConfig.ALLOWED_ORIGINS[0])
        response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.set('Access-Control-Allow-Credentials', 'true')
        response.headers.set('Vary', 'Origin')
    
    return response

# The rest of the file is the same as app.py
# Routes and other functionality...

# Import the routes from the original app.py
from app import register, admin_register, login, admin_login, get_profile, update_profile
from app import get_items, place_bid, get_item_bids, create_item, get_admin_items, get_all_bids
from app import test, index, favicon

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
