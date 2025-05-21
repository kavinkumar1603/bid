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

# MongoDB Configuration
db_name = MongoDBConfig.get_db_name()
print(f"Using MongoDB database: {db_name}")  # Debug log

# MongoDB connection with proper timeout and retry settings
try:
    print("Attempting to connect to MongoDB...")
    print(f"Connection type: {MongoDBConfig.CONNECTION_TYPE}")

    # Get the appropriate connection URI
    connection_uri = MongoDBConfig.get_connection_uri()
    print(f"Using connection URI: {connection_uri}")

    # Try to connect to MongoDB
    try:
        # For local connection, use minimal options
        if MongoDBConfig.CONNECTION_TYPE == 'local':
            client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
        else:
            # For Atlas connections, try different SSL configurations
            try:
                print("Trying Atlas connection with standard SSL settings...")
                # First try with standard SSL settings
                client = MongoClient(
                    connection_uri,
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
                print("Trying Atlas connection with permissive SSL settings...")
                client = MongoClient(
                    connection_uri,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    tlsAllowInvalidCertificates=True,
                    ssl=True,
                    ssl_cert_reqs=ssl.CERT_NONE
                )

        # Force a connection to verify it works
        client.admin.command('ping')
        db = client.get_database(db_name)
        print(f"Connected to MongoDB ({MongoDBConfig.CONNECTION_TYPE})")

        # List collections to verify connection
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")

        # If connection fails, try local MongoDB as fallback
        if MongoDBConfig.CONNECTION_TYPE != 'local':
            try:
                print("Trying local MongoDB as fallback...")
                client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
                db = client.get_database(db_name)
                print("Connected to local MongoDB (fallback)")
            except Exception as e2:
                print(f"Local MongoDB fallback failed: {str(e2)}")
                raise Exception("All MongoDB connection approaches failed")
        else:
            # If we're already trying local and it failed, raise the exception
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

# Validation functions
def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    return len(password) >= 6

def validate_username(username):
    return len(username) >= 3 and username.isalnum()

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print('Register attempt:', data)  # Debug log

        # Validate required fields
        required_fields = ['username', 'email', 'password', 'phone_number', 'address']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'All fields are required'}), 400

        # Validate field formats
        if not validate_username(data['username']):
            return jsonify({'error': 'Username must be at least 3 characters long and contain only letters and numbers'}), 400

        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        if not validate_password(data['password']):
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        if not validate_phone(data['phone_number']):
            return jsonify({'error': 'Invalid phone number format'}), 400

        # Check for existing username/email
        if users_collection.find_one({'username': data['username']}):
            return jsonify({'error': 'Username already exists'}), 400

        if users_collection.find_one({'email': data['email']}):
            return jsonify({'error': 'Email already exists'}), 400

        user = {
            'username': data['username'],
            'email': data['email'],
            'password_hash': generate_password_hash(data['password']),
            'phone_number': data['phone_number'],
            'address': data['address'],
            'profile_image': None,
            'user_type': 'user',
            'created_at': datetime.now(timezone.utc)
        }

        result = users_collection.insert_one(user)
        return jsonify({
            'message': 'User created successfully',
            'user_id': str(result.inserted_id)
        }), 201

    except Exception as e:
        print('Registration error:', str(e))  # Debug log
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    try:
        data = request.get_json()
        print('Admin register attempt:', data)  # Debug log

        # Validate required fields
        required_fields = ['username', 'email', 'password', 'phone_number', 'address', 'admin_code']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'error': 'All fields are required'}), 400

        # Validate field formats
        if not validate_username(data['username']):
            return jsonify({'error': 'Username must be at least 3 characters long and contain only letters and numbers'}), 400

        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        if not validate_password(data['password']):
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        if not validate_phone(data['phone_number']):
            return jsonify({'error': 'Invalid phone number format'}), 400

        # Verify admin code
        if data['admin_code'] != 'ADMIN123':
            return jsonify({'error': 'Invalid admin code'}), 401

        # Check for existing username/email
        if users_collection.find_one({'username': data['username']}):
            return jsonify({'error': 'Username already exists'}), 400

        if users_collection.find_one({'email': data['email']}):
            return jsonify({'error': 'Email already exists'}), 400

        user = {
            'username': data['username'],
            'email': data['email'],
            'password_hash': generate_password_hash(data['password']),
            'phone_number': data['phone_number'],
            'address': data['address'],
            'profile_image': None,
            'user_type': 'admin',
            'created_at': datetime.now(timezone.utc)
        }

        result = users_collection.insert_one(user)
        return jsonify({
            'message': 'Admin created successfully',
            'user_id': str(result.inserted_id)
        }), 201

    except Exception as e:
        print('Admin registration error:', str(e))  # Debug log
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({'status': 'success'})

        # Get the origin from the request
        origin = request.headers.get('Origin')

        # If the origin is in our allowed origins, set it specifically
        if origin in CORSConfig.ALLOWED_ORIGINS:
            response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            # Default to the first allowed origin
            response.headers.add('Access-Control-Allow-Origin', CORSConfig.ALLOWED_ORIGINS[0])

        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        data = request.get_json()
        print('Login attempt:', data)  # Debug log

        # Validate required fields
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400

        user = users_collection.find_one({'username': data['username']})
        if user and check_password_hash(user['password_hash'], data['password']):
            access_token = create_access_token(identity=str(user['_id']))
            print('Login success:', user['username'])  # Debug log

            response = jsonify({
                'access_token': access_token,
                'user': {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'email': user['email'],
                    'phone_number': user['phone_number'],
                    'address': user['address'],
                    'profile_image': user['profile_image'],
                    'user_type': user['user_type']
                }
            })

            # Ensure CORS headers are set
            for origin in CORSConfig.ALLOWED_ORIGINS:
                if request.headers.get('Origin') == origin:
                    response.headers.add('Access-Control-Allow-Origin', origin)
                    break
            else:
                # If no match, use the first allowed origin
                response.headers.add('Access-Control-Allow-Origin', CORSConfig.ALLOWED_ORIGINS[0])

            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

        print('Login failed')  # Debug log
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print('Login error:', str(e))  # Debug log
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({'status': 'success'})

        # Get the origin from the request
        origin = request.headers.get('Origin')

        # If the origin is in our allowed origins, set it specifically
        if origin in CORSConfig.ALLOWED_ORIGINS:
            response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            # Default to the first allowed origin
            response.headers.add('Access-Control-Allow-Origin', CORSConfig.ALLOWED_ORIGINS[0])

        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        data = request.get_json()
        print('Admin login attempt:', data)  # Debug log

        # Validate required fields
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400

        user = users_collection.find_one({'username': data['username']})
        # Also check if the user is an admin
        if user and user.get('user_type') == 'admin' and check_password_hash(user['password_hash'], data['password']):
            access_token = create_access_token(identity=str(user['_id']))
            print('Admin login success:', user['username'])  # Debug log

            response = jsonify({
                'access_token': access_token,
                'user': {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'email': user['email'],
                    'phone_number': user['phone_number'],
                    'address': user['address'],
                    'profile_image': user['profile_image'],
                    'user_type': user['user_type']
                }
            })

            # Ensure CORS headers are set
            for origin in CORSConfig.ALLOWED_ORIGINS:
                if request.headers.get('Origin') == origin:
                    response.headers.add('Access-Control-Allow-Origin', origin)
                    break
            else:
                # If no match, use the first allowed origin
                response.headers.add('Access-Control-Allow-Origin', CORSConfig.ALLOWED_ORIGINS[0])

            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

        print('Admin login failed')  # Debug log
        return jsonify({'error': 'Invalid credentials or not an admin'}), 401
    except Exception as e:
        print('Admin login error:', str(e))  # Debug log
        return jsonify({'error': 'Admin login failed. Please try again.'}), 500

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user = get_jwt_identity()
        user = users_collection.find_one({'_id': ObjectId(current_user)})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user['_id'] = str(user['_id'])
        return jsonify(user)
    except Exception as e:
        print(f"Error in get_profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.form
    update_data = {}

    if 'username' in data:
        update_data['username'] = data['username']
    if 'email' in data:
        update_data['email'] = data['email']

    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            update_data['profile_image'] = filename

    if update_data:
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

    return jsonify({'message': 'Profile updated successfully'})

@app.route('/api/items', methods=['GET'])
def get_items():
    items = list(items_collection.find({'status': 'active'}))
    return jsonify([{
        'id': str(item['_id']),
        'name': item['name'],
        'description': item['description'],
        'current_price': item['current_price'],
        'end_time': item['end_time'].isoformat(),
        'image_url': item['image_url'],
        'seller_id': str(item['seller_id'])
    } for item in items])

@app.route('/api/items/<item_id>/bid', methods=['POST'])
@jwt_required()
def place_bid(item_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if not item or item['status'] != 'active':
        return jsonify({'error': 'Item not found or auction ended'}), 404

    if item['end_time'] < datetime.now(timezone.utc):
        return jsonify({'error': 'Auction has ended'}), 400

    if data['amount'] <= item['current_price']:
        return jsonify({'error': 'Bid must be higher than current price'}), 400

    bid = {
        'amount': data['amount'],
        'user_id': ObjectId(user_id),
        'item_id': ObjectId(item_id),
        'is_auto_bid': data.get('is_auto_bid', False),
        'max_amount': data.get('max_amount'),
        'timestamp': datetime.now(timezone.utc)
    }

    bids_collection.insert_one(bid)

    items_collection.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'current_price': data['amount']}}
    )

    return jsonify({'message': 'Bid placed successfully'})

@app.route('/api/items/<item_id>/bids', methods=['GET'])
def get_item_bids(item_id):
    bids = list(bids_collection.find({'item_id': ObjectId(item_id)}).sort('timestamp', -1))
    return jsonify([{
        'id': str(bid['_id']),
        'amount': bid['amount'],
        'timestamp': bid['timestamp'].isoformat(),
        'user_id': str(bid['user_id']),
        'is_auto_bid': bid['is_auto_bid']
    } for bid in bids])

@app.route('/api/items', methods=['POST'])
@jwt_required()
def create_item():
    user_id = get_jwt_identity()
    data = request.form

    item = {
        'name': data['name'],
        'description': data['description'],
        'starting_price': float(data['starting_price']),
        'current_price': float(data['starting_price']),
        'end_time': datetime.fromisoformat(data['end_time']),
        'seller_id': ObjectId(user_id),
        'status': 'active',
        'created_at': datetime.now(timezone.utc)
    }

    if 'image' in request.files:
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            item['image_url'] = filename

    result = items_collection.insert_one(item)
    return jsonify({'message': 'Item created successfully', 'item_id': str(result.inserted_id)}), 201

@app.route('/api/admin/items', methods=['GET'])
@jwt_required()
def get_admin_items():
    try:
        items = list(items_collection.find())
        for item in items:
            item['_id'] = str(item['_id'])
        return jsonify(items)
    except Exception as e:
        print(f"Error in get_admin_items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/bids', methods=['GET'])
@jwt_required()
def get_all_bids():
    try:
        pipeline = [
            {
                '$lookup': {
                    'from': 'items',
                    'localField': 'item_id',
                    'foreignField': '_id',
                    'as': 'item'
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {
                '$unwind': '$item'
            },
            {
                '$unwind': '$user'
            },
            {
                '$project': {
                    '_id': {'$toString': '$_id'},
                    'amount': 1,
                    'timestamp': 1,
                    'item': {
                        '_id': {'$toString': '$item._id'},
                        'name': 1,
                        'description': 1
                    },
                    'user': {
                        '_id': {'$toString': '$user._id'},
                        'username': 1,
                        'email': 1
                    }
                }
            },
            {
                '$sort': {'timestamp': -1}
            }
        ]

        bids = list(bids_collection.aggregate(pipeline))
        return jsonify(bids)
    except Exception as e:
        print(f"Error in get_all_bids: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    return "Test route working"

@app.route('/')
def index():
    return "Auction Backend API is running. Try /api/items or /test."

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

# Install dependencies
# RUN pip install -r requirements.txt