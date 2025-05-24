"""
Create an active auction item with future end time for testing bidding.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson import ObjectId

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MongoDBConfig

def create_active_auction():
    """Create an active auction item with future end time."""
    print("\n===== Creating Active Auction Item =====")
    
    # Use local MongoDB
    uri = MongoDBConfig.LOCAL_URI
    db_name = MongoDBConfig.LOCAL_DB_NAME
    
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
        
        # Create an active auction item with future end time
        future_time = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days from now
        
        active_item = {
            'name': 'Ancient Greek Sculpture Replica',
            'description': 'A beautiful replica of an ancient Greek sculpture. Perfect for collectors and art enthusiasts. This auction is active and accepting bids.',
            'starting_price': 100.0,
            'current_price': 100.0,
            'end_time': future_time,
            'seller_id': user_id,
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'image_url': None,
            'category': 'Sculptures',
            'condition': 'Excellent',
            'location': 'Art Gallery, NY'
        }
        
        # Insert the item
        result = items_collection.insert_one(active_item)
        print(f"✅ Active auction created with ID: {result.inserted_id}")
        print(f"   Name: {active_item['name']}")
        print(f"   Starting Price: ${active_item['starting_price']}")
        print(f"   End Time: {active_item['end_time']}")
        print(f"   Status: {active_item['status']}")
        
        # Verify the item was created and is active
        created_item = items_collection.find_one({'_id': result.inserted_id})
        if created_item:
            now = datetime.now(timezone.utc)
            if created_item['end_time'] > now:
                time_remaining = created_item['end_time'] - now
                print(f"✅ Auction is active! Time remaining: {time_remaining}")
                print(f"✅ You can now test bidding on this item")
                return str(result.inserted_id)
            else:
                print("❌ End time is in the past")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error creating active auction: {str(e)}")
        return False

if __name__ == "__main__":
    item_id = create_active_auction()
    
    if item_id:
        print(f"\n🎉 Active auction created successfully!")
        print(f"Item ID: {item_id}")
        print(f"\n📝 Test this auction:")
        print(f"1. Go to http://localhost:3001")
        print(f"2. Login with: testuser / password123")
        print(f"3. Find the 'Ancient Greek Sculpture Replica' item")
        print(f"4. Click 'View Details' and try placing a bid")
        print(f"5. The bid should work since the auction is active")
    else:
        print("\n❌ Failed to create active auction!")
