"""
Create a fresh item with future end time for testing bidding.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson import ObjectId

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MongoDBConfig

def create_fresh_item():
    """Create a fresh item with future end time."""
    print("\n===== Creating Fresh Item for Bidding Test =====")
    
    # Use local MongoDB
    uri = MongoDBConfig.LOCAL_URI
    db_name = MongoDBConfig.LOCAL_DB_NAME
    
    print(f"Connection URI: {uri}")
    print(f"Database name: {db_name}")
    
    try:
        # Connect to local MongoDB
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to local MongoDB")
        
        # Get collections
        items_collection = db['items']
        users_collection = db['users']
        
        # Get a test user
        test_user = users_collection.find_one({'username': 'testuser'})
        if not test_user:
            print("❌ Test user not found")
            return False
        
        user_id = test_user['_id']
        print(f"✅ Found test user: {test_user['username']} (ID: {user_id})")
        
        # Create a fresh item with future end time
        future_time = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days from now
        
        fresh_item = {
            'name': 'Test Antique Vase',
            'description': 'A beautiful test vase for bidding functionality testing. This item has a future end time.',
            'starting_price': 50.0,
            'current_price': 50.0,
            'end_time': future_time,
            'seller_id': user_id,
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'image_url': None,
            'category': 'Ceramics',
            'condition': 'Excellent',
            'location': 'Test Location'
        }
        
        # Insert the item
        result = items_collection.insert_one(fresh_item)
        print(f"✅ Fresh item created with ID: {result.inserted_id}")
        print(f"   Name: {fresh_item['name']}")
        print(f"   Starting Price: ${fresh_item['starting_price']}")
        print(f"   End Time: {fresh_item['end_time']}")
        print(f"   Status: {fresh_item['status']}")
        
        # Verify the item was created
        created_item = items_collection.find_one({'_id': result.inserted_id})
        if created_item:
            print("✅ Item creation verified")
            
            # Check if the end time is in the future
            now = datetime.now(timezone.utc)
            if created_item['end_time'] > now:
                print("✅ End time is in the future - bidding should work")
                time_remaining = created_item['end_time'] - now
                print(f"   Time remaining: {time_remaining}")
            else:
                print("❌ End time is in the past")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating fresh item: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_fresh_item()
    
    if success:
        print("\n🎉 Fresh item created successfully!")
        print("You can now test bidding functionality with this new item.")
    else:
        print("\n❌ Failed to create fresh item!")
