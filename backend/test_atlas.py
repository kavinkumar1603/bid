from pymongo import MongoClient
import certifi
import ssl
import time

# MongoDB Atlas connection string
atlas_uri = 'mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
direct_uri = 'mongodb://kavin88701:mGmvb7QugKUb0O7z@ac-zm7hkzz-shard-00-00.zik7il3.mongodb.net:27017,ac-zm7hkzz-shard-00-01.zik7il3.mongodb.net:27017,ac-zm7hkzz-shard-00-02.zik7il3.mongodb.net:27017/?ssl=true&replicaSet=atlas-ixvlxl-shard-0&authSource=admin&retryWrites=true&w=majority'

def test_atlas_connection():
    print("Testing MongoDB Atlas connection...")
    
    # Try SRV connection
    try:
        print("Trying SRV connection...")
        client = MongoClient(
            atlas_uri,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        client.admin.command('ping')
        print("SRV connection successful!")
        
        # Get database and collections
        db = client.get_database('Newpy')
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Create a test bid
        bids_collection = db['bids']
        test_bid = {
            'amount': 100.0,
            'user_id': 'test_user_id',
            'item_id': 'test_item_id',
            'timestamp': time.time()
        }
        result = bids_collection.insert_one(test_bid)
        print(f"Test bid inserted with ID: {result.inserted_id}")
        
        # Close connection
        client.close()
        return True
    except Exception as e:
        print(f"SRV connection failed: {str(e)}")
    
    # Try direct connection
    try:
        print("Trying direct connection...")
        client = MongoClient(
            direct_uri,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        client.admin.command('ping')
        print("Direct connection successful!")
        
        # Get database and collections
        db = client.get_database('Newpy')
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Create a test bid
        bids_collection = db['bids']
        test_bid = {
            'amount': 100.0,
            'user_id': 'test_user_id',
            'item_id': 'test_item_id',
            'timestamp': time.time()
        }
        result = bids_collection.insert_one(test_bid)
        print(f"Test bid inserted with ID: {result.inserted_id}")
        
        # Close connection
        client.close()
        return True
    except Exception as e:
        print(f"Direct connection failed: {str(e)}")
    
    return False

if __name__ == "__main__":
    if test_atlas_connection():
        print("MongoDB Atlas connection test passed!")
    else:
        print("MongoDB Atlas connection test failed!")
