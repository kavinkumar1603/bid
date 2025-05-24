"""
Script to migrate data from local MongoDB to MongoDB Atlas.
"""
import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId
import json

# Add the current directory to the path so we can import the config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MongoDBConfig

def migrate_data():
    """Migrate data from local MongoDB to Atlas."""
    print("\n===== Migrating Data from Local to Atlas =====")
    
    # Local MongoDB connection
    local_uri = MongoDBConfig.LOCAL_URI
    local_db_name = MongoDBConfig.LOCAL_DB_NAME
    
    # Atlas MongoDB connection
    atlas_uri = MongoDBConfig.ATLAS_URI
    atlas_db_name = MongoDBConfig.ATLAS_DB_NAME
    
    print(f"Local URI: {local_uri}")
    print(f"Local DB: {local_db_name}")
    print(f"Atlas URI: {atlas_uri}")
    print(f"Atlas DB: {atlas_db_name}")
    
    try:
        # Connect to local MongoDB
        print("\n1. Connecting to local MongoDB...")
        local_client = MongoClient(local_uri, serverSelectionTimeoutMS=5000)
        local_db = local_client[local_db_name]
        
        # Test local connection
        local_client.admin.command('ping')
        print("✅ Connected to local MongoDB")
        
        # Connect to Atlas
        print("\n2. Connecting to MongoDB Atlas...")
        atlas_client = MongoClient(
            atlas_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000,
            retryWrites=True,
            w="majority"
        )
        atlas_db = atlas_client[atlas_db_name]
        
        # Test Atlas connection
        atlas_client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
        
        # Collections to migrate
        collections_to_migrate = ['users', 'items', 'bids']
        
        for collection_name in collections_to_migrate:
            print(f"\n3. Migrating {collection_name} collection...")
            
            # Get data from local
            local_collection = local_db[collection_name]
            local_data = list(local_collection.find())
            
            print(f"   Found {len(local_data)} documents in local {collection_name}")
            
            if len(local_data) > 0:
                # Get Atlas collection
                atlas_collection = atlas_db[collection_name]
                
                # Clear existing data in Atlas (optional)
                atlas_collection.delete_many({})
                print(f"   Cleared existing data in Atlas {collection_name}")
                
                # Insert data into Atlas
                if local_data:
                    result = atlas_collection.insert_many(local_data)
                    print(f"   ✅ Inserted {len(result.inserted_ids)} documents into Atlas {collection_name}")
                else:
                    print(f"   No data to migrate for {collection_name}")
            else:
                print(f"   No data found in local {collection_name}")
        
        print("\n✅ Data migration completed successfully!")
        
        # Verify migration
        print("\n4. Verifying migration...")
        for collection_name in collections_to_migrate:
            local_count = local_db[collection_name].count_documents({})
            atlas_count = atlas_db[collection_name].count_documents({})
            print(f"   {collection_name}: Local={local_count}, Atlas={atlas_count}")
            
            if local_count == atlas_count:
                print(f"   ✅ {collection_name} migration verified")
            else:
                print(f"   ❌ {collection_name} migration mismatch")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False

def create_atlas_items():
    """Create items directly in Atlas if migration fails."""
    print("\n===== Creating Items Directly in Atlas =====")
    
    try:
        # Connect to Atlas
        atlas_uri = MongoDBConfig.ATLAS_URI
        atlas_db_name = MongoDBConfig.ATLAS_DB_NAME
        
        client = MongoClient(
            atlas_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000,
            retryWrites=True,
            w="majority"
        )
        db = client[atlas_db_name]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
        
        # Create collections
        items_collection = db['items']
        users_collection = db['users']
        
        # Create test items
        test_items = [
            {
                'name': 'Vintage Pocket Watch',
                'description': 'A beautiful antique pocket watch from the 1920s. Gold-plated with intricate engravings.',
                'starting_price': 150.0,
                'current_price': 150.0,
                'end_time': datetime.now(timezone.utc).replace(day=29),  # End in a few days
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
                'end_time': datetime.now(timezone.utc).replace(day=27),
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
                'end_time': datetime.now(timezone.utc).replace(day=31),
                'seller_id': ObjectId('000000000000000000000000'),
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'image_url': None,
                'category': 'Ceramics',
                'condition': 'Excellent',
                'location': 'San Francisco, CA'
            }
        ]
        
        # Clear existing items
        items_collection.delete_many({})
        
        # Insert test items
        result = items_collection.insert_many(test_items)
        print(f"✅ Created {len(result.inserted_ids)} items in Atlas")
        
        # Create test user if not exists
        existing_user = users_collection.find_one({'username': 'testuser'})
        if not existing_user:
            from werkzeug.security import generate_password_hash
            
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
            
            users_collection.insert_one(test_user)
            print("✅ Created test user in Atlas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating items in Atlas: {str(e)}")
        return False

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Migrate data from local to Atlas")
    print("2. Create new items directly in Atlas")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = migrate_data()
    elif choice == "2":
        success = create_atlas_items()
    else:
        print("Invalid choice")
        success = False
    
    if success:
        print("\n🎉 Operation completed successfully!")
        print("You can now restart the backend with Atlas configuration.")
    else:
        print("\n❌ Operation failed!")
