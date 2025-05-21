"""
Test script for MongoDB Atlas connection using different methods.
This script attempts various approaches to connect to MongoDB Atlas.
"""
import sys
import platform
import ssl
import certifi
import urllib3
import socket
import dns.resolver
from pymongo import MongoClient

# Check if ServerApi is available (newer versions of pymongo)
try:
    from pymongo.server_api import ServerApi
    HAS_SERVER_API = True
except ImportError:
    HAS_SERVER_API = False
    print("Note: pymongo.server_api is not available in your version of PyMongo. Method 2 will be skipped.")

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
        import os
        if os.path.exists(cert_path):
            print(f"✅ Certifi file exists")
            # Check file size to ensure it's not empty
            size = os.path.getsize(cert_path)
            print(f"Certifi file size: {size} bytes")
        else:
            print(f"❌ Certifi file does not exist")
    except Exception as e:
        print(f"❌ Error checking certifi: {str(e)}")

def test_dns_resolution(hostname):
    """Test DNS resolution for MongoDB Atlas hostnames."""
    print(f"\nTesting DNS resolution for {hostname}...")
    try:
        # Try standard DNS resolution
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ Standard DNS resolution successful: {hostname} -> {ip_address}")
    except Exception as e:
        print(f"❌ Standard DNS resolution failed: {str(e)}")

    try:
        # Try DNS resolver
        answers = dns.resolver.resolve(hostname, 'A')
        print(f"✅ DNS resolver successful: {hostname} ->", end=" ")
        for rdata in answers:
            print(rdata.address, end=" ")
        print()
    except Exception as e:
        print(f"❌ DNS resolver failed: {str(e)}")

def test_connection_method1():
    """Test MongoDB Atlas connection using method 1 (standard)."""
    print("\nTesting MongoDB Atlas connection using method 1 (standard)...")

    connection_string = "mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    try:
        # Create a new client and connect to the server
        client = MongoClient(connection_string)

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Method 1: Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return True
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)}")
        return False

def test_connection_method2():
    """Test MongoDB Atlas connection using method 2 (with server API)."""
    print("\nTesting MongoDB Atlas connection using method 2 (with server API)...")

    if not HAS_SERVER_API:
        print("❌ Method 2 skipped: ServerApi not available in your version of PyMongo")
        return False

    connection_string = "mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    try:
        # Create a new client and connect to the server
        client = MongoClient(connection_string, server_api=ServerApi('1'))

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Method 2: Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return True
    except Exception as e:
        print(f"❌ Method 2 failed: {str(e)}")
        return False

def test_connection_method3():
    """Test MongoDB Atlas connection using method 3 (with SSL settings)."""
    print("\nTesting MongoDB Atlas connection using method 3 (with SSL settings)...")

    connection_string = "mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    try:
        # Create a new client with SSL settings
        client = MongoClient(
            connection_string,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Method 3: Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return True
    except Exception as e:
        print(f"❌ Method 3 failed: {str(e)}")
        return False

def test_connection_method4():
    """Test MongoDB Atlas connection using method 4 (with permissive SSL settings)."""
    print("\nTesting MongoDB Atlas connection using method 4 (with permissive SSL settings)...")

    connection_string = "mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    try:
        # Create a new client with permissive SSL settings
        client = MongoClient(
            connection_string,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            serverSelectionTimeoutMS=5000
        )

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Method 4: Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return True
    except Exception as e:
        print(f"❌ Method 4 failed: {str(e)}")
        return False

def test_connection_method5():
    """Test MongoDB Atlas connection using method 5 (direct connection string)."""
    print("\nTesting MongoDB Atlas connection using method 5 (direct connection string)...")

    # Using the standard connection string for method 5 as well since we don't have the direct connection details for the new cluster
    connection_string = "mongodb+srv://kavin88701:mGmvb7QugKUb0O7z@cluster0.zik7il3.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

    try:
        # Create a new client with direct connection string
        client = MongoClient(
            connection_string,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            serverSelectionTimeoutMS=5000
        )

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("✅ Method 5: Successfully connected to MongoDB Atlas!")

        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        return True
    except Exception as e:
        print(f"❌ Method 5 failed: {str(e)}")
        return False

def main():
    """Test multiple connection approaches to MongoDB Atlas."""
    print("MongoDB Atlas Connection Tester")
    print("===============================")

    # Print system information
    print_system_info()

    # Test DNS resolution
    test_dns_resolution('cluster0.zik7il3.mongodb.net')

    # Test different connection methods
    methods = [
        test_connection_method1,
        test_connection_method2,
        test_connection_method3,
        test_connection_method4,
        test_connection_method5
    ]

    success = False
    for i, method in enumerate(methods, 1):
        if method():
            success = True
            print(f"\n✅ Method {i} successfully connected to MongoDB Atlas!")
            break

    if not success:
        print("\n❌ All connection methods failed.")
        print("\nRecommendations:")
        print("1. Check your MongoDB Atlas dashboard to ensure:")
        print("   - Your IP address is whitelisted")
        print("   - Your username and password are correct")
        print("   - Your cluster is active and not paused")
        print("2. Try using a VPN or different network")
        print("3. Check if your system's SSL/TLS configuration is up to date")
        print("4. Try using a different Python version")
        print("5. Try connecting from a different device or operating system")

if __name__ == "__main__":
    main()
