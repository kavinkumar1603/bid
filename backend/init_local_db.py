"""
Initialize the local MongoDB database with the necessary collections and indexes.
This script should be run once to set up the local MongoDB database.
"""
from pymongo import MongoClient
from config import MongoDBConfig
import os

def init_local_db():
    """Initialize the local MongoDB database with the necessary collections and indexes."""
    print("Initializing local MongoDB database...")
    
    # Connect to local MongoDB
    client = MongoClient(MongoDBConfig.LOCAL_URI)
    db = client[MongoDBConfig.LOCAL_DB_NAME]
    
    # Create collections if they don't exist
    if 'users' not in db.list_collection_names():
        print("Creating users collection...")
        users = db.create_collection('users')
        # Create indexes for better performance
        users.create_index([('username', 1)], unique=True)
        users.create_index([('email', 1)], unique=True)
        print("Created users collection with indexes")
    
    if 'items' not in db.list_collection_names():
        print("Creating items collection...")
        items = db.create_collection('items')
        # Create indexes for better performance
        items.create_index([('seller_id', 1)])
        items.create_index([('status', 1)])
        print("Created items collection with indexes")
    
    if 'bids' not in db.list_collection_names():
        print("Creating bids collection...")
        bids = db.create_collection('bids')
        # Create indexes for better performance
        bids.create_index([('item_id', 1)])
        bids.create_index([('user_id', 1)])
        print("Created bids collection with indexes")
    
    # Print all collections
    print(f"Available collections: {db.list_collection_names()}")
    print("Local MongoDB database initialization complete")

if __name__ == "__main__":
    # Set environment variable to use local MongoDB
    os.environ['MONGODB_CONNECTION_TYPE'] = 'local'
    init_local_db()
