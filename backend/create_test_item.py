"""
Script to create a test item in the MongoDB database.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson import ObjectId

# Add the current directory to the path so we can import the config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MongoDBConfig

def create_test_item():
    """Create a test item in the MongoDB database."""
    print("\n===== Creating Test Item =====")
    
    # Get the connection URI from the config
    uri = MongoDBConfig.ATLAS_URI
    db_name = MongoDBConfig.ATLAS_DB_NAME
    
    print(f"Connection URI: {uri}")
    print(f"Database name: {db_name}")
    
    try:
        # Connect to MongoDB
        client = MongoClient(uri)
        db = client[db_name]
        
        # Create the items collection if it doesn't exist
        if 'items' not in db.list_collection_names():
            db.create_collection('items')
            print("Created items collection")
        
        # Create a test item
        items_collection = db['items']
        
        # Create a test item
        test_item = {
            'name': 'Test Item',
            'description': 'This is a test item created for testing purposes.',
            'starting_price': 10.0,
            'current_price': 10.0,
            'end_time': datetime.now(timezone.utc) + timedelta(days=7),
            'seller_id': ObjectId('000000000000000000000000'),  # Placeholder seller ID
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'image_url': None,
            'category': 'Test',
            'condition': 'New',
            'location': 'Test Location'
        }
        
        # Insert the test item
        result = items_collection.insert_one(test_item)
        print(f"✅ Test item inserted with ID: {result.inserted_id}")
        
        # Verify the item was inserted
        item = items_collection.find_one({'_id': result.inserted_id})
        if item:
            print("✅ Successfully verified test item was inserted")
            print(f"Item name: {item['name']}")
            print(f"Item price: {item['current_price']}")
            print(f"Item end time: {item['end_time']}")
        else:
            print("❌ Failed to verify test item was inserted")
        
    except Exception as e:
        print(f"❌ Error creating test item: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_test_item()
    if success:
        print("\n✅ Test item created successfully!")
    else:
        print("\n❌ Failed to create test item!")
