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
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=60000,
                    socketTimeoutMS=60000,
                    tlsCAFile=certifi.where(),
                    retryWrites=True,
                    w="majority"
                )
                # Test the connection
                client.admin.command('ping')
                print("Connected to MongoDB Atlas with standard SSL settings")
            except Exception as e1:
                print(f"Standard SSL connection failed: {str(e1)}")

                try:
                    # Try with direct connection string
                    print("Trying Atlas connection with direct connection string...")
                    direct_uri = MongoDBConfig.DIRECT_URI
                    client = MongoClient(
                        direct_uri,
                        serverSelectionTimeoutMS=30000,
                        connectTimeoutMS=60000,
                        socketTimeoutMS=60000,
                        tlsCAFile=certifi.where(),
                        retryWrites=True,
                        w="majority",
                        connect=True,  # Force a connection attempt
                        directConnection=False,  # Don't use direct connection with SRV
                        appName="NewpyAuction"  # Add app name for monitoring
                    )
                    # Test the connection
                    client.admin.command('ping')
                    print("Connected to MongoDB Atlas with direct connection string")
                except Exception as e2:
                    print(f"Direct connection failed: {str(e2)}")

                    # Third try with more permissive SSL settings
                    print("Trying Atlas connection with permissive SSL settings...")
                    client = MongoClient(
                        connection_uri,
                        serverSelectionTimeoutMS=30000,
                        connectTimeoutMS=60000,
                        socketTimeoutMS=60000,
                        tlsAllowInvalidCertificates=True,
                        retryWrites=True,
                        w="majority",
                        connect=True,  # Force a connection attempt
                        appName="NewpyAuction"  # Add app name for monitoring
                    )

        # Force a connection to verify it works
        try:
            client.admin.command('ping')
            db = client.get_database(db_name)
            print(f"Connected to MongoDB ({MongoDBConfig.CONNECTION_TYPE})")

            # Create the collections if they don't exist
            if 'users' not in db.list_collection_names():
                db.create_collection('users')
                print("Created users collection")

            if 'items' not in db.list_collection_names():
                db.create_collection('items')
                print("Created items collection")

            if 'bids' not in db.list_collection_names():
                db.create_collection('bids')
                print("Created bids collection")
        except Exception as e:
            print(f"Error verifying connection: {str(e)}")
            raise e

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
    print(f"Serving file: {filename} from {app.config['UPLOAD_FOLDER']}")
    try:
        # Ensure the uploads directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Check if the file exists
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return "File not found", 404

        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return str(e), 500

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
    try:
        print("Fetching items...")
        items = list(items_collection.find({'status': 'active'}))
        print(f"Found {len(items)} active items")

        result = [{
            'id': str(item['_id']),
            'name': item['name'],
            'description': item['description'],
            'current_price': item['current_price'],
            'end_time': item['end_time'].isoformat(),
            'image_url': item.get('image_url'),
            'seller_id': str(item['seller_id']),
            'category': item.get('category', ''),
            'condition': item.get('condition', ''),
            'location': item.get('location', '')
        } for item in items]

        print(f"Returning {len(result)} items")
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['GET'])
def get_item(item_id):
    try:
        print(f"Fetching item with ID: {item_id}")

        # Find the item by ID
        try:
            item = items_collection.find_one({'_id': ObjectId(item_id)})
        except Exception as e:
            print(f"Error finding item: {str(e)}")
            return jsonify({'error': f'Invalid item ID: {str(e)}'}), 400

        if not item:
            print(f"Item not found with ID: {item_id}")
            return jsonify({'error': 'Item not found'}), 404

        # Convert the item to a dictionary with string IDs
        result = {
            'id': str(item['_id']),
            'name': item['name'],
            'description': item['description'],
            'current_price': item['current_price'],
            'starting_price': item.get('starting_price', item['current_price']),
            'end_time': item['end_time'].isoformat(),
            'image_url': item.get('image_url'),
            'seller_id': str(item['seller_id']),
            'status': item.get('status', 'active'),
            'category': item.get('category', ''),
            'condition': item.get('condition', ''),
            'location': item.get('location', ''),
            'created_at': item.get('created_at', datetime.now(timezone.utc)).isoformat()
        }

        print(f"Item found: {result['name']}")
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>/bid', methods=['POST', 'OPTIONS'])
@jwt_required()
def place_bid(item_id):
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    try:
        print(f"Placing bid on item {item_id}")
        user_id = get_jwt_identity()
        print(f"User ID: {user_id}")

        # Get request data
        data = request.get_json()
        print(f"Bid data: {data}")

        if not data or 'amount' not in data:
            print("Missing bid amount")
            return jsonify({'error': 'Bid amount is required'}), 400

        # Find the item
        try:
            item = items_collection.find_one({'_id': ObjectId(item_id)})
        except Exception as e:
            print(f"Error finding item: {str(e)}")
            return jsonify({'error': f'Invalid item ID: {str(e)}'}), 400

        if not item:
            print(f"Item not found with ID: {item_id}")
            return jsonify({'error': 'Item not found'}), 404

        if item.get('status') != 'active':
            print(f"Item is not active: {item.get('status')}")
            return jsonify({'error': 'Auction has ended'}), 400

        # Convert end_time to aware datetime if it's naive
        end_time = item['end_time']
        if end_time.tzinfo is None:
            print("Converting naive end_time to aware datetime")
            end_time = end_time.replace(tzinfo=timezone.utc)

        # Check if auction has ended
        now = datetime.now(timezone.utc)
        if end_time < now:
            print(f"Auction has ended. End time: {end_time}, Current time: {now}")
            return jsonify({'error': 'Auction has ended'}), 400

        # Validate bid amount
        try:
            bid_amount = float(data['amount'])
        except (ValueError, TypeError):
            print(f"Invalid bid amount: {data['amount']}")
            return jsonify({'error': 'Invalid bid amount'}), 400

        if bid_amount <= item['current_price']:
            print(f"Bid too low: {bid_amount} <= {item['current_price']}")
            return jsonify({'error': f"Bid must be higher than current price (${item['current_price']})"}), 400

        # Create bid object
        try:
            # Convert user_id and item_id to ObjectId
            user_obj_id = ObjectId(user_id)
            item_obj_id = ObjectId(item_id)

            bid = {
                'amount': bid_amount,
                'user_id': user_obj_id,
                'item_id': item_obj_id,
                'is_auto_bid': data.get('is_auto_bid', False),
                'max_amount': data.get('max_amount'),
                'timestamp': now
            }
            print(f"Created bid object with user_id={user_obj_id}, item_id={item_obj_id}")
        except Exception as e:
            print(f"Error creating bid object: {str(e)}")
            return jsonify({'error': f'Invalid ID format: {str(e)}'}), 400

        # Insert bid into local MongoDB
        try:
            print("Inserting bid into local database...")
            print(f"Bid data: {bid}")
            result = bids_collection.insert_one(bid)
            print(f"Bid inserted with ID: {result.inserted_id}")

            # Verify the bid was inserted
            inserted_bid = bids_collection.find_one({'_id': result.inserted_id})
            if inserted_bid:
                print(f"Verified bid insertion: {inserted_bid}")
            else:
                print("WARNING: Bid insertion verification failed!")

            # Try to insert the bid into MongoDB Atlas as well
            try:
                from atlas_connector import atlas
                print("Attempting to insert bid into MongoDB Atlas...")

                # Create a copy of the bid for Atlas
                atlas_bid = bid.copy()
                # Convert ObjectId to string for JSON serialization
                atlas_bid['_id'] = str(result.inserted_id)

                # Connect to Atlas
                if atlas.connect():
                    # Insert the bid
                    atlas_bid_id = atlas.insert_bid(atlas_bid)
                    if atlas_bid_id:
                        print(f"Bid also inserted into MongoDB Atlas with ID: {atlas_bid_id}")
                    else:
                        print("Failed to insert bid into MongoDB Atlas")
                else:
                    print("Failed to connect to MongoDB Atlas")
            except Exception as e:
                print(f"Error inserting bid into MongoDB Atlas: {str(e)}")
                # Continue even if Atlas insertion fails
                pass

        except Exception as e:
            print(f"Error inserting bid into local database: {str(e)}")
            raise e

        # Update item price
        try:
            print(f"Updating item price to {bid_amount}...")
            update_result = items_collection.update_one(
                {'_id': ObjectId(item_id)},
                {'$set': {'current_price': bid_amount}}
            )
            print(f"Item price updated: {update_result.modified_count} document(s) modified")

            # Verify the item price was updated
            updated_item = items_collection.find_one({'_id': ObjectId(item_id)})
            if updated_item:
                print(f"Verified item price update: {updated_item['current_price']}")
            else:
                print("WARNING: Item price update verification failed!")
        except Exception as e:
            print(f"Error updating item price: {str(e)}")
            raise e

        return jsonify({'message': 'Bid placed successfully', 'bid_id': str(result.inserted_id)}), 200

    except Exception as e:
        print(f"Error placing bid: {str(e)}")
        return jsonify({'error': f'Failed to place bid: {str(e)}'}), 500

@app.route('/api/items/<item_id>/bids', methods=['GET'])
def get_item_bids(item_id):
    try:
        print(f"Fetching bids for item {item_id}")

        # Find the bids
        try:
            print(f"Querying bids for item_id: {item_id}")

            # Check if bids_collection is valid
            if bids_collection is None:
                print("Error: bids_collection is not initialized")
                return jsonify({'error': 'Database connection error'}), 500

            # List all collections to verify
            collections = db.list_collection_names()
            print(f"Available collections: {collections}")

            # Count all bids in the collection
            total_bids = bids_collection.count_documents({})
            print(f"Total bids in collection: {total_bids}")

            # Find bids for this item
            try:
                item_obj_id = ObjectId(item_id)
                print(f"Converted item_id to ObjectId: {item_obj_id}")

                # First check if any bids exist with this item_id in local MongoDB
                count = bids_collection.count_documents({'item_id': item_obj_id})
                print(f"Found {count} bids with item_id={item_obj_id} in local MongoDB")

                # Get the bids from local MongoDB
                local_bids = list(bids_collection.find({'item_id': item_obj_id}).sort('timestamp', -1))
                print(f"Retrieved {len(local_bids)} bids for item {item_id} from local MongoDB")

                # Try to get bids from MongoDB Atlas as well
                atlas_bids = []
                try:
                    from atlas_connector import atlas
                    print("Attempting to retrieve bids from MongoDB Atlas...")

                    # Connect to Atlas
                    if atlas.connect():
                        # Get bids for this item
                        atlas_bids = atlas.get_bids_for_item(item_id)
                        print(f"Retrieved {len(atlas_bids)} bids for item {item_id} from MongoDB Atlas")
                    else:
                        print("Failed to connect to MongoDB Atlas")
                except Exception as e:
                    print(f"Error retrieving bids from MongoDB Atlas: {str(e)}")
                    # Continue with local bids if Atlas retrieval fails

                # Combine bids from both sources, removing duplicates
                all_bids = local_bids.copy()

                # Add Atlas bids that don't exist in local bids
                local_bid_ids = [str(bid['_id']) for bid in local_bids]
                for atlas_bid in atlas_bids:
                    if atlas_bid['_id'] not in local_bid_ids:
                        # Convert string IDs back to ObjectId for consistency
                        atlas_bid['_id'] = ObjectId(atlas_bid['_id'])
                        atlas_bid['user_id'] = ObjectId(atlas_bid['user_id'])
                        atlas_bid['item_id'] = ObjectId(atlas_bid['item_id'])
                        all_bids.append(atlas_bid)

                # Sort combined bids by timestamp
                bids = sorted(all_bids, key=lambda x: x['timestamp'], reverse=True)
                print(f"Combined {len(bids)} bids from local MongoDB and MongoDB Atlas")

            except Exception as e:
                print(f"Error processing bids: {str(e)}")
                return jsonify({'error': f'Error processing bids: {str(e)}'}), 400

            # Print bid details for debugging
            for i, bid in enumerate(bids):
                print(f"Bid {i+1}: ID={bid.get('_id')}, Amount={bid.get('amount')}, User={bid.get('user_id')}, Time={bid.get('timestamp')}")

        except Exception as e:
            print(f"Error finding bids: {str(e)}")
            return jsonify({'error': f'Invalid item ID: {str(e)}'}), 400

        # Convert bids to JSON-serializable format
        result = []
        for bid in bids:
            # Ensure timestamp has timezone info
            timestamp = bid['timestamp']
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            bid_data = {
                'id': str(bid['_id']),
                'amount': bid['amount'],
                'timestamp': timestamp.isoformat(),
                'user_id': str(bid['user_id']),
                'is_auto_bid': bid.get('is_auto_bid', False)
            }
            result.append(bid_data)

        return jsonify(result)

    except Exception as e:
        print(f"Error getting bids: {str(e)}")
        return jsonify({'error': f'Failed to get bids: {str(e)}'}), 500

@app.route('/api/items', methods=['POST'])
@jwt_required()
def create_item():
    try:
        print("Creating new item...")
        user_id = get_jwt_identity()
        print(f"User ID: {user_id}")

        # Check if form data is present
        if not request.form:
            print("No form data received")
            return jsonify({'error': 'No form data received'}), 400

        data = request.form
        print(f"Received form data: {list(data.keys())}")

        # Validate required fields
        required_fields = ['name', 'description', 'starting_price', 'end_time']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400

        # Create item object
        try:
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

            # Add optional fields if present
            if 'category' in data:
                item['category'] = data['category']
            if 'condition' in data:
                item['condition'] = data['condition']
            if 'location' in data:
                item['location'] = data['location']

            print(f"Item object created: {item}")
        except ValueError as e:
            print(f"Error creating item object: {str(e)}")
            return jsonify({'error': f'Invalid data format: {str(e)}'}), 400

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            print(f"Image file received: {file.filename}")

            if file and file.filename:
                try:
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                    # Save the file
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    # Check if file was saved successfully
                    if os.path.exists(file_path):
                        print(f"Image saved successfully at: {file_path}")
                        item['image_url'] = filename
                    else:
                        print(f"Failed to save image at: {file_path}")
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    # Continue without image if there's an error
                    pass

        # Insert item into database
        result = items_collection.insert_one(item)
        print(f"Item created with ID: {result.inserted_id}")

        return jsonify({
            'message': 'Item created successfully',
            'item_id': str(result.inserted_id)
        }), 201

    except Exception as e:
        print(f"Error creating item: {str(e)}")
        return jsonify({'error': f'Failed to create item: {str(e)}'}), 500

@app.route('/api/items/<item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    try:
        print(f"Updating item with ID: {item_id}")
        user_id = get_jwt_identity()
        print(f"User ID: {user_id}")

        # Check if form data is present
        if not request.form:
            print("No form data received")
            return jsonify({'error': 'No form data received'}), 400

        data = request.form
        print(f"Received form data: {list(data.keys())}")

        # Find the item
        item = items_collection.find_one({'_id': ObjectId(item_id)})
        if not item:
            print(f"Item not found with ID: {item_id}")
            return jsonify({'error': 'Item not found'}), 404

        # Create update object
        update_data = {}

        # Update basic fields if present
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'category' in data:
            update_data['category'] = data['category']
        if 'condition' in data:
            update_data['condition'] = data['condition']
        if 'location' in data:
            update_data['location'] = data['location']

        # Update numeric fields if present
        if 'starting_price' in data:
            try:
                update_data['starting_price'] = float(data['starting_price'])
                # Only update current price if it's still at the original starting price
                if item['current_price'] == item['starting_price']:
                    update_data['current_price'] = float(data['starting_price'])
            except ValueError:
                print(f"Invalid starting price: {data['starting_price']}")
                return jsonify({'error': 'Invalid starting price'}), 400

        # Update date fields if present
        if 'end_time' in data:
            try:
                update_data['end_time'] = datetime.fromisoformat(data['end_time'])
            except ValueError:
                print(f"Invalid end time format: {data['end_time']}")
                return jsonify({'error': 'Invalid end time format'}), 400

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            print(f"Image file received: {file.filename}")

            if file and file.filename:
                try:
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                    # Save the file
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    # Check if file was saved successfully
                    if os.path.exists(file_path):
                        print(f"Image saved successfully at: {file_path}")
                        update_data['image_url'] = filename
                    else:
                        print(f"Failed to save image at: {file_path}")
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    # Continue without updating image if there's an error
                    pass

        # Update the item
        if update_data:
            result = items_collection.update_one(
                {'_id': ObjectId(item_id)},
                {'$set': update_data}
            )
            print(f"Item updated: {result.modified_count} document(s) modified")

            if result.modified_count == 0:
                print("No changes made to the item")
                return jsonify({'message': 'No changes made to the item'}), 200

            return jsonify({'message': 'Item updated successfully'}), 200
        else:
            print("No valid update data provided")
            return jsonify({'message': 'No changes made to the item'}), 200

    except Exception as e:
        print(f"Error updating item: {str(e)}")
        return jsonify({'error': f'Failed to update item: {str(e)}'}), 500

@app.route('/api/items/<item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    try:
        print(f"Deleting item with ID: {item_id}")
        user_id = get_jwt_identity()

        # Find the item
        item = items_collection.find_one({'_id': ObjectId(item_id)})
        if not item:
            print(f"Item not found with ID: {item_id}")
            return jsonify({'error': 'Item not found'}), 404

        # Delete the item
        result = items_collection.delete_one({'_id': ObjectId(item_id)})

        if result.deleted_count == 0:
            print("Item not deleted")
            return jsonify({'error': 'Failed to delete item'}), 500

        print(f"Item deleted successfully")
        return jsonify({'message': 'Item deleted successfully'}), 200

    except Exception as e:
        print(f"Error deleting item: {str(e)}")
        return jsonify({'error': f'Failed to delete item: {str(e)}'}), 500

@app.route('/api/admin/items', methods=['GET'])
@jwt_required()
def get_admin_items():
    try:
        print("Fetching admin items...")
        user_id = get_jwt_identity()
        print(f"Admin user ID: {user_id}")

        # Check if items_collection is valid
        if items_collection is None:
            print("Error: items_collection is not initialized")
            return jsonify({'error': 'Database connection error'}), 500

        try:
            # Test the database connection
            db.command('ping')
            print("Database connection is working")
        except Exception as db_error:
            print(f"Database connection error: {str(db_error)}")
            return jsonify({'error': 'Database connection error'}), 500

        try:
            # Get all items
            items = list(items_collection.find())
            print(f"Found {len(items)} items")

            # Convert ObjectId to string
            for item in items:
                item['_id'] = str(item['_id'])

            return jsonify(items)
        except Exception as query_error:
            print(f"Error querying items: {str(query_error)}")
            return jsonify({'error': f'Error querying items: {str(query_error)}'}), 500

    except Exception as e:
        print(f"Error in get_admin_items: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

# Install dependencies
# RUN pip install -r requirements.txt