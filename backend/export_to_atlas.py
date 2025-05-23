"""
Export Local MongoDB Data to MongoDB Atlas

This script exports data from the local MongoDB database to MongoDB Atlas.
It handles connection retries, error logging, and provides a simple interface
for exporting data.
"""

import os
import time
import certifi
from pymongo import MongoClient, errors
from bson import ObjectId
from datetime import datetime, timezone
import json

# Local MongoDB connection string
LOCAL_URI = 'mongodb://localhost:27017/'
LOCAL_DB_NAME = 'Newpy'

# MongoDB Atlas connection string
ATLAS_URI = 'mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
ATLAS_DB_NAME = 'Newpy'

def connect_to_local():
    """Connect to local MongoDB."""
    print(f"Connecting to local MongoDB at {LOCAL_URI}")
    try:
        client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("Connected to local MongoDB")
        return client
    except Exception as e:
        print(f"Error connecting to local MongoDB: {str(e)}")
        return None

def connect_to_atlas():
    """Connect to MongoDB Atlas with retry logic."""
    print(f"Connecting to MongoDB Atlas at {ATLAS_URI}")
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Connection attempt {attempt}/{max_retries}...")
            
            # Create MongoDB client with optimized settings
            client = MongoClient(
                ATLAS_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                tlsCAFile=certifi.where(),
                retryWrites=True,
                w="majority",
                appName="NewpyExport"
            )
            
            # Test the connection
            client.admin.command('ping')
            print("Connected to MongoDB Atlas")
            return client
            
        except errors.ConnectionFailure as e:
            print(f"Connection attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All connection attempts failed")
                return None
        
        except Exception as e:
            print(f"Unexpected error during connection: {str(e)}")
            return None

def export_collection(local_client, atlas_client, collection_name):
    """Export a collection from local MongoDB to MongoDB Atlas."""
    print(f"Exporting collection: {collection_name}")
    
    try:
        # Get collections
        local_db = local_client.get_database(LOCAL_DB_NAME)
        atlas_db = atlas_client.get_database(ATLAS_DB_NAME)
        
        local_collection = local_db[collection_name]
        atlas_collection = atlas_db[collection_name]
        
        # Count documents
        local_count = local_collection.count_documents({})
        atlas_count = atlas_collection.count_documents({})
        
        print(f"Local {collection_name} count: {local_count}")
        print(f"Atlas {collection_name} count: {atlas_count}")
        
        # Get all documents from local collection
        local_docs = list(local_collection.find({}))
        print(f"Retrieved {len(local_docs)} documents from local {collection_name}")
        
        # Export documents to Atlas
        exported_count = 0
        for doc in local_docs:
            # Check if document already exists in Atlas
            doc_id = doc['_id']
            existing_doc = atlas_collection.find_one({'_id': doc_id})
            
            if not existing_doc:
                # Insert document into Atlas
                atlas_collection.insert_one(doc)
                exported_count += 1
        
        print(f"Exported {exported_count} documents to Atlas {collection_name}")
        
        # Verify export
        atlas_count_after = atlas_collection.count_documents({})
        print(f"Atlas {collection_name} count after export: {atlas_count_after}")
        
        return exported_count
    
    except Exception as e:
        print(f"Error exporting {collection_name}: {str(e)}")
        return 0

def export_all_collections():
    """Export all collections from local MongoDB to MongoDB Atlas."""
    print("Starting export from local MongoDB to MongoDB Atlas")
    
    # Connect to local MongoDB
    local_client = connect_to_local()
    if not local_client:
        print("Failed to connect to local MongoDB")
        return False
    
    # Connect to MongoDB Atlas
    atlas_client = connect_to_atlas()
    if not atlas_client:
        print("Failed to connect to MongoDB Atlas")
        local_client.close()
        return False
    
    try:
        # Get collections
        local_db = local_client.get_database(LOCAL_DB_NAME)
        collections = local_db.list_collection_names()
        print(f"Found {len(collections)} collections in local MongoDB: {collections}")
        
        # Export each collection
        total_exported = 0
        for collection_name in collections:
            exported = export_collection(local_client, atlas_client, collection_name)
            total_exported += exported
        
        print(f"Export complete. Total documents exported: {total_exported}")
        
        # Close connections
        local_client.close()
        atlas_client.close()
        
        return True
    
    except Exception as e:
        print(f"Error during export: {str(e)}")
        
        # Close connections
        if local_client:
            local_client.close()
        if atlas_client:
            atlas_client.close()
        
        return False

if __name__ == "__main__":
    if export_all_collections():
        print("Export successful")
    else:
        print("Export failed")
