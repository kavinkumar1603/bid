"""
Test script to verify MongoDB connection string.
This script attempts to connect to MongoDB using different approaches.
"""
import sys
import time
from pymongo import MongoClient
import certifi
import ssl

def test_connection(connection_string, **kwargs):
    """Test a MongoDB connection with the given connection string and options."""
    print(f"\nTesting connection with: {connection_string}")
    print(f"Additional options: {kwargs}")
    
    try:
        # Create client with the connection string
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000, **kwargs)
        
        # Try to get server info
        server_info = client.server_info()
        print(f"✅ Connection successful!")
        print(f"Server info: {server_info.get('version', 'Unknown')}")
        
        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")
        
        # Try to access the specific database
        db = client.get_database('Newpy')
        collections = db.list_collection_names()
        print(f"Collections in 'Newpy': {collections}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def main():
    """Test multiple connection approaches."""
    print("MongoDB Connection String Tester")
    print("================================")
    
    # Connection strings to test
    connection_strings = [
        # Standard Atlas connection string
        'mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/Newpy?retryWrites=true&w=majority',
        
        # Direct connection with explicit hosts
        'mongodb://kavin88701:nR1Cc1SOsgRiXedQ@ac-uowy13k-shard-00-00.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-01.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-02.01myarq.mongodb.net:27017/Newpy?ssl=true&replicaSet=atlas-ixvlnj-shard-0&authSource=admin&retryWrites=true&w=majority',
        
        # Local MongoDB (if available)
        'mongodb://localhost:27017/'
    ]
    
    # Connection options to test
    connection_options = [
        # Default options
        {},
        
        # With TLS CA file
        {'tlsCAFile': certifi.where()},
        
        # With disabled certificate verification (insecure, for testing only)
        {'ssl': True, 'ssl_cert_reqs': ssl.CERT_NONE, 'tlsAllowInvalidCertificates': True},
        
        # With longer timeouts
        {'serverSelectionTimeoutMS': 10000, 'connectTimeoutMS': 30000, 'socketTimeoutMS': 30000}
    ]
    
    # Test each connection string with each set of options
    success = False
    for conn_str in connection_strings:
        for options in connection_options:
            if test_connection(conn_str, **options):
                success = True
                print("\n✅ Found a working connection configuration!")
                print(f"Connection string: {conn_str}")
                print(f"Options: {options}")
                
                # Ask if user wants to continue testing
                if input("\nContinue testing other configurations? (y/n): ").lower() != 'y':
                    return
    
    if not success:
        print("\n❌ All connection attempts failed.")
        print("Possible issues:")
        print("1. Network connectivity problems")
        print("2. Firewall blocking MongoDB connections")
        print("3. MongoDB Atlas username/password incorrect")
        print("4. MongoDB Atlas IP whitelist doesn't include your IP")
        print("5. MongoDB Atlas cluster is paused or not available")
        print("\nRecommendations:")
        print("- Check your MongoDB Atlas dashboard")
        print("- Verify username and password")
        print("- Add your current IP to the MongoDB Atlas IP whitelist")
        print("- Try from a different network")

if __name__ == "__main__":
    main()
