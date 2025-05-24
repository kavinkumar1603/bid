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

    # Use local MongoDB for testing
    uri = "mongodb://localhost:27017/"
    db_name = "Newpy"

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

        # Create multiple test items
        test_items = [
            {
                'name': 'Vintage Pocket Watch',
                'description': 'A beautiful antique pocket watch from the 1920s. Gold-plated with intricate engravings.',
                'starting_price': 150.0,
                'current_price': 150.0,
                'end_time': datetime.now(timezone.utc) + timedelta(days=5),
                'seller_id': ObjectId('000000000000000000000000'),
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'image_url': None,
                'category': 'Watches',
                'condition': 'Excellent',
                'location': 'New York, NY'
            },
            {
                'name': 'Victorian Era Jewelry Box',
                'description': 'Ornate wooden jewelry box with velvet interior. Perfect for collectors.',
                'starting_price': 75.0,
                'current_price': 75.0,
                'end_time': datetime.now(timezone.utc) + timedelta(days=3),
                'seller_id': ObjectId('000000000000000000000000'),
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'image_url': None,
                'category': 'Furniture',
                'condition': 'Good',
                'location': 'Boston, MA'
            },
            {
                'name': 'Antique Chinese Vase',
                'description': 'Ming Dynasty style porcelain vase with blue and white patterns.',
                'starting_price': 300.0,
                'current_price': 300.0,
                'end_time': datetime.now(timezone.utc) + timedelta(days=7),
                'seller_id': ObjectId('000000000000000000000000'),
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'image_url': None,
                'category': 'Ceramics',
                'condition': 'Excellent',
                'location': 'San Francisco, CA'
            },
            {
                'name': 'Rare First Edition Book',
                'description': 'First edition of "Pride and Prejudice" by Jane Austen. Leather bound.',
                'starting_price': 500.0,
                'current_price': 500.0,
                'end_time': datetime.now(timezone.utc) + timedelta(days=10),
                'seller_id': ObjectId('000000000000000000000000'),
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'image_url': None,
                'category': 'Books',
                'condition': 'Very Good',
                'location': 'London, UK'
            }
        ]

        # Insert all test items
        for i, test_item in enumerate(test_items):
            result = items_collection.insert_one(test_item)
            print(f"✅ Test item {i+1} inserted with ID: {result.inserted_id}")
            print(f"   Name: {test_item['name']}")
            print(f"   Price: ${test_item['current_price']}")

        print(f"\n✅ Successfully created {len(test_items)} test items")

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
