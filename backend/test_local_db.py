from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import sys
import json

# Local MongoDB connection string
local_uri = 'mongodb://localhost:27017/'
db_name = 'Newpy'

def test_local_db():
    print("Testing local MongoDB connection and bid storage...")
    
    try:
        # Connect to local MongoDB
        print(f"Connecting to local MongoDB at {local_uri}")
        client = MongoClient(local_uri, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        client.admin.command('ping')
        print("Connected to local MongoDB")
        
        # Get database
        db = client.get_database(db_name)
        print(f"Connected to database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Create collections if they don't exist
        if 'bids' not in collections:
            db.create_collection('bids')
            print("Created bids collection")
        
        if 'items' not in collections:
            db.create_collection('items')
            print("Created items collection")
            
        if 'users' not in collections:
            db.create_collection('users')
            print("Created users collection")
        
        # Get collections
        bids_collection = db['bids']
        items_collection = db['items']
        users_collection = db['users']
        
        # Count existing documents
        bid_count = bids_collection.count_documents({})
        item_count = items_collection.count_documents({})
        user_count = users_collection.count_documents({})
        
        print(f"Current document counts:")
        print(f"  - Bids: {bid_count}")
        print(f"  - Items: {item_count}")
        print(f"  - Users: {user_count}")
        
        # Create a test user if none exists
        if user_count == 0:
            test_user = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': 'pbkdf2:sha256:150000$abc123',
                'phone_number': '1234567890',
                'address': '123 Test St',
                'profile_image': None,
                'user_type': 'user',
                'created_at': datetime.now(timezone.utc)
            }
            user_result = users_collection.insert_one(test_user)
            print(f"Created test user with ID: {user_result.inserted_id}")
            user_id = user_result.inserted_id
        else:
            # Get an existing user
            user = users_collection.find_one({})
            user_id = user['_id']
            print(f"Using existing user with ID: {user_id}")
        
        # Create a test item if none exists
        if item_count == 0:
            test_item = {
                'name': 'Test Item',
                'description': 'This is a test item',
                'starting_price': 10.0,
                'current_price': 10.0,
                'end_time': datetime.now(timezone.utc).replace(day=datetime.now().day + 7),
                'seller_id': user_id,
                'status': 'active',
                'created_at': datetime.now(timezone.utc)
            }
            item_result = items_collection.insert_one(test_item)
            print(f"Created test item with ID: {item_result.inserted_id}")
            item_id = item_result.inserted_id
        else:
            # Get an existing item
            item = items_collection.find_one({})
            item_id = item['_id']
            print(f"Using existing item with ID: {item_id}")
        
        # Create a test bid
        test_bid = {
            'amount': 15.0 + bid_count,  # Make each test bid unique
            'user_id': user_id,
            'item_id': item_id,
            'is_auto_bid': False,
            'timestamp': datetime.now(timezone.utc)
        }
        
        # Insert the test bid
        bid_result = bids_collection.insert_one(test_bid)
        print(f"Created test bid with ID: {bid_result.inserted_id}")
        
        # Verify the bid was inserted
        inserted_bid = bids_collection.find_one({'_id': bid_result.inserted_id})
        if inserted_bid:
            print(f"Verified bid insertion: ID={inserted_bid['_id']}, Amount={inserted_bid['amount']}")
        else:
            print("WARNING: Bid insertion verification failed!")
            
        # Get all bids for the item
        item_bids = list(bids_collection.find({'item_id': item_id}).sort('timestamp', -1))
        print(f"Found {len(item_bids)} bids for item {item_id}")
        
        # Print bid details
        for i, bid in enumerate(item_bids):
            print(f"Bid {i+1}: ID={bid['_id']}, Amount={bid['amount']}, Time={bid['timestamp']}")
        
        # Close connection
        client.close()
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if test_local_db():
        print("Local MongoDB connection and bid storage test passed!")
        sys.exit(0)
    else:
        print("Local MongoDB connection and bid storage test failed!")
        sys.exit(1)
