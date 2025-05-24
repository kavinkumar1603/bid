"""
Simple script to create test data directly in MongoDB Atlas.
This bypasses local data migration and creates fresh data in Atlas.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash
import ssl

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import MongoDBConfig

def create_atlas_data():
    """Create test data directly in MongoDB Atlas."""
    print("\n===== Creating Test Data in MongoDB Atlas =====")
    
    atlas_uri = MongoDBConfig.ATLAS_URI
    atlas_db_name = MongoDBConfig.ATLAS_DB_NAME
    
    print(f"Atlas URI: {atlas_uri}")
    print(f"Atlas DB: {atlas_db_name}")
    
    try:
        # Try different connection approaches
        connection_successful = False
        client = None
        
        # Approach 1: Standard connection
        try:
            print("\n1. Trying standard Atlas connection...")
            client = MongoClient(
                atlas_uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                retryWrites=True,
                w="majority",
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE
            )
            client.admin.command('ping')
            print("✅ Standard connection successful!")
            connection_successful = True
        except Exception as e:
            print(f"❌ Standard connection failed: {str(e)}")
        
        # Approach 2: Connection with TLS disabled
        if not connection_successful:
            try:
                print("\n2. Trying connection with relaxed SSL...")
                client = MongoClient(
                    atlas_uri,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=20000,
                    retryWrites=True,
                    w="majority",
                    tlsAllowInvalidCertificates=True,
                    tlsAllowInvalidHostnames=True
                )
                client.admin.command('ping')
                print("✅ Relaxed SSL connection successful!")
                connection_successful = True
            except Exception as e:
                print(f"❌ Relaxed SSL connection failed: {str(e)}")
        
        # Approach 3: Basic connection
        if not connection_successful:
            try:
                print("\n3. Trying basic connection...")
                client = MongoClient(atlas_uri, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                print("✅ Basic connection successful!")
                connection_successful = True
            except Exception as e:
                print(f"❌ Basic connection failed: {str(e)}")
        
        if not connection_successful:
            print("\n❌ All connection attempts failed!")
            print("\n🔧 Troubleshooting suggestions:")
            print("1. Check your internet connection")
            print("2. Verify Atlas cluster is running")
            print("3. Check IP whitelist in Atlas (add 0.0.0.0/0 for testing)")
            print("4. Verify username/password in connection string")
            print("5. Try using MongoDB Compass to connect")
            return False
        
        # Get database
        db = client[atlas_db_name]
        
        # Create collections
        users_collection = db['users']
        items_collection = db['items']
        bids_collection = db['bids']
        
        print(f"\n4. Creating test data in Atlas database: {atlas_db_name}")
        
        # Clear existing data
        print("   Clearing existing data...")
        users_collection.delete_many({})
        items_collection.delete_many({})
        bids_collection.delete_many({})
        
        # Create test users
        print("   Creating test users...")
        test_users = [
            {
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': generate_password_hash('password123'),
                'phone_number': '+1234567890',
                'address': '123 Test Street, Test City, Test Country',
                'profile_image': None,
                'user_type': 'user',
                'created_at': datetime.now(timezone.utc)
            },
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password_hash': generate_password_hash('admin123'),
                'phone_number': '+0987654321',
                'address': '456 Admin Street, Admin City, Admin Country',
                'profile_image': None,
                'user_type': 'admin',
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        users_result = users_collection.insert_many(test_users)
        print(f"   ✅ Created {len(users_result.inserted_ids)} users")
        
        # Create test items
        print("   Creating test items...")
        test_items = [
            {
                'name': 'Vintage Pocket Watch',
                'description': 'A beautiful antique pocket watch from the 1920s. Gold-plated with intricate engravings.',
                'starting_price': 150.0,
                'current_price': 150.0,
                'end_time': datetime.now(timezone.utc) + timedelta(days=5),
                'seller_id': users_result.inserted_ids[0],
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
                'seller_id': users_result.inserted_ids[0],
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
                'seller_id': users_result.inserted_ids[0],
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
                'seller_id': users_result.inserted_ids[0],
                'status': 'active',
                'created_at': datetime.now(timezone.utc),
                'image_url': None,
                'category': 'Books',
                'condition': 'Very Good',
                'location': 'London, UK'
            }
        ]
        
        items_result = items_collection.insert_many(test_items)
        print(f"   ✅ Created {len(items_result.inserted_ids)} items")
        
        # Verify data
        print("\n5. Verifying data in Atlas...")
        user_count = users_collection.count_documents({})
        item_count = items_collection.count_documents({})
        bid_count = bids_collection.count_documents({})
        
        print(f"   Users: {user_count}")
        print(f"   Items: {item_count}")
        print(f"   Bids: {bid_count}")
        
        print("\n✅ Test data created successfully in MongoDB Atlas!")
        print("\n📝 Test credentials:")
        print("   Username: testuser")
        print("   Password: password123")
        print("   Admin Username: admin")
        print("   Admin Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating data in Atlas: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = create_atlas_data()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart your backend with Atlas configuration:")
        print("   $env:MONGODB_CONNECTION_TYPE=\"atlas\"; python app.py")
        print("2. Refresh your frontend to see the Atlas data")
    else:
        print("\n❌ Setup failed!")
        print("Consider using MongoDB Compass for manual data migration.")
