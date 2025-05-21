from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
import json
import re

app = Flask(__name__)



CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# MongoDB Configuration
mongo_db_name = 'test_db' if os.environ.get('TESTING') == '1' else 'Newpy'
print(f"Using MongoDB database: {mongo_db_name}")  # Debug log
client = MongoClient('mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['Newpy']
print(db.list_collection_names())
users_collection = db['users']
items_collection = db['items']
bids_collection = db['bids']

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Initialize JWTd
jwt = JWTManager(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to convert ObjectId to string
def serialize_mongo_id(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

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
            'created_at': datetime.utcnow()
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
            'created_at': datetime.utcnow()
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
        # CORS preflight request
        return '', 200
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
            return jsonify({
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
        print('Login failed')  # Debug log
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print('Login error:', str(e))  # Debug log
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        # CORS preflight request
        return '', 200
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
            return jsonify({
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
    
    if item['end_time'] < datetime.utcnow():
        return jsonify({'error': 'Auction has ended'}), 400
    
    if data['amount'] <= item['current_price']:
        return jsonify({'error': 'Bid must be higher than current price'}), 400
    
    bid = {
        'amount': data['amount'],
        'user_id': ObjectId(user_id),
        'item_id': ObjectId(item_id),
        'is_auto_bid': data.get('is_auto_bid', False),
        'max_amount': data.get('max_amount'),
        'timestamp': datetime.utcnow()
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
        'created_at': datetime.utcnow()
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