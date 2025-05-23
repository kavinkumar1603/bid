"""
MongoDB Atlas Connector

This module provides a reliable connection to MongoDB Atlas.
It handles connection retries, error logging, and provides a simple interface
for interacting with MongoDB Atlas collections.
"""

import os
import time
import certifi
from pymongo import MongoClient, errors
from bson import ObjectId
from datetime import datetime, timezone

# MongoDB Atlas connection string
ATLAS_URI = 'mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
DB_NAME = 'Newpy'

class AtlasConnector:
    """MongoDB Atlas connector with retry logic and error handling."""
    
    def __init__(self, uri=ATLAS_URI, db_name=DB_NAME, max_retries=3, retry_delay=2):
        """Initialize the connector with connection parameters."""
        self.uri = uri
        self.db_name = db_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        self.db = None
        self.connected = False
    
    def connect(self):
        """Connect to MongoDB Atlas with retry logic."""
        print(f"Connecting to MongoDB Atlas at {self.uri}")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"Connection attempt {attempt}/{self.max_retries}...")
                
                # Create MongoDB client with optimized settings
                self.client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=20000,
                    tlsCAFile=certifi.where(),
                    retryWrites=True,
                    w="majority",
                    appName="NewpyAuction"
                )
                
                # Test the connection
                self.client.admin.command('ping')
                print("Connected to MongoDB Atlas")
                
                # Get database
                self.db = self.client.get_database(self.db_name)
                print(f"Connected to database: {self.db_name}")
                
                # List collections
                collections = self.db.list_collection_names()
                print(f"Available collections: {collections}")
                
                # Create collections if they don't exist
                self._ensure_collections()
                
                self.connected = True
                return True
                
            except errors.ConnectionFailure as e:
                print(f"Connection attempt {attempt} failed: {str(e)}")
                if attempt < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print("All connection attempts failed")
                    return False
            
            except Exception as e:
                print(f"Unexpected error during connection: {str(e)}")
                return False
    
    def _ensure_collections(self):
        """Ensure that all required collections exist."""
        required_collections = ['users', 'items', 'bids']
        existing_collections = self.db.list_collection_names()
        
        for collection_name in required_collections:
            if collection_name not in existing_collections:
                print(f"Creating collection: {collection_name}")
                self.db.create_collection(collection_name)
    
    def get_collection(self, collection_name):
        """Get a collection by name, ensuring connection first."""
        if not self.connected:
            if not self.connect():
                print(f"Failed to get collection {collection_name}: Not connected")
                return None
        
        return self.db[collection_name]
    
    def insert_bid(self, bid_data):
        """Insert a bid into the bids collection."""
        bids_collection = self.get_collection('bids')
        if not bids_collection:
            return None
        
        try:
            # Ensure proper ObjectId conversion
            if 'user_id' in bid_data and not isinstance(bid_data['user_id'], ObjectId):
                bid_data['user_id'] = ObjectId(bid_data['user_id'])
            
            if 'item_id' in bid_data and not isinstance(bid_data['item_id'], ObjectId):
                bid_data['item_id'] = ObjectId(bid_data['item_id'])
            
            # Ensure timestamp
            if 'timestamp' not in bid_data:
                bid_data['timestamp'] = datetime.now(timezone.utc)
            
            # Insert the bid
            result = bids_collection.insert_one(bid_data)
            print(f"Bid inserted with ID: {result.inserted_id}")
            
            # Verify the insertion
            inserted_bid = bids_collection.find_one({'_id': result.inserted_id})
            if inserted_bid:
                print(f"Verified bid insertion: {inserted_bid['_id']}")
                return result.inserted_id
            else:
                print("WARNING: Bid insertion verification failed")
                return None
                
        except Exception as e:
            print(f"Error inserting bid: {str(e)}")
            return None
    
    def get_bids_for_item(self, item_id):
        """Get all bids for a specific item."""
        bids_collection = self.get_collection('bids')
        if not bids_collection:
            return []
        
        try:
            # Convert item_id to ObjectId if needed
            if not isinstance(item_id, ObjectId):
                item_id = ObjectId(item_id)
            
            # Find bids for this item
            bids = list(bids_collection.find({'item_id': item_id}).sort('timestamp', -1))
            print(f"Found {len(bids)} bids for item {item_id}")
            
            # Convert ObjectId to string for JSON serialization
            for bid in bids:
                bid['_id'] = str(bid['_id'])
                bid['user_id'] = str(bid['user_id'])
                bid['item_id'] = str(bid['item_id'])
            
            return bids
            
        except Exception as e:
            print(f"Error getting bids for item: {str(e)}")
            return []
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.connected = False
            print("MongoDB Atlas connection closed")

# Create a singleton instance
atlas = AtlasConnector()

# Test the connection if this module is run directly
if __name__ == "__main__":
    if atlas.connect():
        print("Connection test successful")
        
        # Insert a test bid
        test_bid = {
            'amount': 100.0,
            'user_id': ObjectId('000000000000000000000001'),
            'item_id': ObjectId('000000000000000000000002'),
            'is_auto_bid': False,
            'timestamp': datetime.now(timezone.utc)
        }
        
        bid_id = atlas.insert_bid(test_bid)
        if bid_id:
            print(f"Test bid inserted successfully with ID: {bid_id}")
        
        # Get bids for the test item
        bids = atlas.get_bids_for_item('000000000000000000000002')
        print(f"Retrieved {len(bids)} bids for test item")
        
        atlas.close()
    else:
        print("Connection test failed")
