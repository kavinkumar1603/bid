"""
Connect to MongoDB Atlas using the latest PyMongo version.
This script attempts to connect to MongoDB Atlas using various approaches.
"""
import os
import sys
import platform
import ssl
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def print_system_info():
    """Print system information for debugging."""
    print("\nSystem Information:")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")

    # Check if certifi is properly installed
    try:
        cert_path = certifi.where()
        print(f"Certifi path: {cert_path}")
        # Check if the file exists
        if os.path.exists(cert_path):
            print(f"✅ Certifi file exists")
            # Check file size to ensure it's not empty
            size = os.path.getsize(cert_path)
            print(f"Certifi file size: {size} bytes")
        else:
            print(f"❌ Certifi file does not exist")
    except Exception as e:
        print(f"❌ Error checking certifi: {str(e)}")

def test_connection():
    """Test connection to MongoDB Atlas."""
    print("\nTesting connection to MongoDB Atlas...")

    # Connection string
    uri = "mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    # Create a new client and connect to the server
    try:
        print("Approach 1: Using Server API version 1")
        client = MongoClient(uri, server_api=ServerApi('1'))

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return client
    except Exception as e:
        print(f"❌ Approach 1 failed: {str(e)}")

    try:
        print("\nApproach 2: Using TLS CA file")
        client = MongoClient(
            uri,
            tlsCAFile=certifi.where()
        )

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return client
    except Exception as e:
        print(f"❌ Approach 2 failed: {str(e)}")

    try:
        print("\nApproach 3: Using SSL with CERT_NONE")
        client = MongoClient(
            uri,
            tls=True,
            tlsAllowInvalidCertificates=True
        )

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return client
    except Exception as e:
        print(f"❌ Approach 3 failed: {str(e)}")

    try:
        print("\nApproach 4: Using direct connection string")
        # Direct connection string
        direct_uri = "mongodb://kavin88701:nR1Cc1SOsgRiXedQ@ac-uowy13k-shard-00-00.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-01.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-02.01myarq.mongodb.net:27017/?ssl=true&replicaSet=atlas-ixvlnj-shard-0&authSource=admin&retryWrites=true&w=majority"

        client = MongoClient(
            direct_uri,
            tls=True,
            tlsAllowInvalidCertificates=True
        )

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return client
    except Exception as e:
        print(f"❌ Approach 4 failed: {str(e)}")

    print("\n❌ All connection approaches failed.")
    print("\nRecommendations:")
    print("1. Check your MongoDB Atlas dashboard to ensure:")
    print("   - Your IP address is whitelisted")
    print("   - Your username and password are correct")
    print("   - Your cluster is active and not paused")
    print("2. Try using a VPN or different network")
    print("3. Check if your system's SSL/TLS configuration is up to date")

    return None

if __name__ == "__main__":
    print_system_info()
    client = test_connection()

    if client:
        print("\nConnection successful! You can now use MongoDB Atlas in your application.")
    else:
        print("\nConnection failed. Please check the recommendations above.")
