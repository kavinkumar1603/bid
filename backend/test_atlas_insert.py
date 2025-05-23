from pymongo import MongoClient
import certifi
from bson import ObjectId
from datetime import datetime, timezone
import time
import sys

# MongoDB Atlas connection string
direct_uri = 'mongodb://kavin88701:mGmvb7QugKUb0O7z@ac-zm7hkzz-shard-00-00.zik7il3.mongodb.net:27017,ac-zm7hkzz-shard-00-01.zik7il3.mongodb.net:27017,ac-zm7hkzz-shard-00-02.zik7il3.mongodb.net:27017/?ssl=true&replicaSet=atlas-ixvlxl-shard-0&authSource=admin&retryWrites=true&w=majority'
atlas_uri = 'mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

def test_atlas_insert():
    print("Testing MongoDB Atlas connection and bid insertion...")
    
    # Try direct connection
    try:
        print("Trying direct connection...")
        client = MongoClient(
            direct_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000,
            tlsCAFile=certifi.where(),
            retryWrites=True,
            w="majority",
            connect=True,
            appName="NewpyAuctionTest"
        )
        
        # Test the connection
        client.admin.command('ping')
        print("Connected to MongoDB Atlas with direct connection")
        
        # Get database
        db = client.get_database('Newpy')
        print(f"Connected to database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Create collections if they don't exist
        if 'bids' not in collections:
            db.create_collection('bids')
            print("Created bids collection")
        
        # Get bids collection
        bids_collection = db['bids']
        
        # Count existing bids
        bid_count = bids_collection.count_documents({})
        print(f"Current bid count: {bid_count}")
        
        # Create a test bid
        test_bid = {
            'amount': 100.0 + bid_count,  # Make each test bid unique
            'user_id': ObjectId('000000000000000000000001'),  # Dummy ObjectId
            'item_id': ObjectId('000000000000000000000002'),  # Dummy ObjectId
            'is_auto_bid': False,
            'timestamp': datetime.now(timezone.utc)
        }
        
        # Insert the test bid
        result = bids_collection.insert_one(test_bid)
        print(f"Test bid inserted with ID: {result.inserted_id}")
        
        # Verify the bid was inserted
        inserted_bid = bids_collection.find_one({'_id': result.inserted_id})
        if inserted_bid:
            print(f"Verified bid insertion: {inserted_bid}")
        else:
            print("WARNING: Bid insertion verification failed!")
        
        # Count bids again to verify
        new_bid_count = bids_collection.count_documents({})
        print(f"New bid count: {new_bid_count}")
        
        # Close connection
        client.close()
        return True
    except Exception as e:
        print(f"Direct connection failed: {str(e)}")
    
    # Try SRV connection
    try:
        print("Trying SRV connection...")
        client = MongoClient(
            atlas_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000,
            tlsCAFile=certifi.where(),
            retryWrites=True,
            w="majority",
            connect=True,
            appName="NewpyAuctionTest"
        )
        
        # Test the connection
        client.admin.command('ping')
        print("Connected to MongoDB Atlas with SRV connection")
        
        # Get database
        db = client.get_database('Newpy')
        print(f"Connected to database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Create collections if they don't exist
        if 'bids' not in collections:
            db.create_collection('bids')
            print("Created bids collection")
        
        # Get bids collection
        bids_collection = db['bids']
        
        # Count existing bids
        bid_count = bids_collection.count_documents({})
        print(f"Current bid count: {bid_count}")
        
        # Create a test bid
        test_bid = {
            'amount': 200.0 + bid_count,  # Make each test bid unique
            'user_id': ObjectId('000000000000000000000001'),  # Dummy ObjectId
            'item_id': ObjectId('000000000000000000000002'),  # Dummy ObjectId
            'is_auto_bid': False,
            'timestamp': datetime.now(timezone.utc)
        }
        
        # Insert the test bid
        result = bids_collection.insert_one(test_bid)
        print(f"Test bid inserted with ID: {result.inserted_id}")
        
        # Verify the bid was inserted
        inserted_bid = bids_collection.find_one({'_id': result.inserted_id})
        if inserted_bid:
            print(f"Verified bid insertion: {inserted_bid}")
        else:
            print("WARNING: Bid insertion verification failed!")
        
        # Count bids again to verify
        new_bid_count = bids_collection.count_documents({})
        print(f"New bid count: {new_bid_count}")
        
        # Close connection
        client.close()
        return True
    except Exception as e:
        print(f"SRV connection failed: {str(e)}")
    
    return False

if __name__ == "__main__":
    if test_atlas_insert():
        print("MongoDB Atlas connection and bid insertion test passed!")
        sys.exit(0)
    else:
        print("MongoDB Atlas connection and bid insertion test failed!")
        sys.exit(1)
