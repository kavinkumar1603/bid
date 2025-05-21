"""
Improved MongoDB Connection Test Script

This script provides a more comprehensive approach to testing MongoDB Atlas connections,
specifically addressing SSL/TLS issues on Windows.
"""
import sys
import time
import platform
import ssl
from pymongo import MongoClient
import certifi
import urllib3
import socket
import dns.resolver

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

def test_ssl_connection(hostname, port=27017):
    """Test direct SSL connection to MongoDB Atlas servers."""
    print(f"\nTesting direct SSL connection to {hostname}:{port}...")
    
    # Create a standard SSL context
    context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ SSL connection successful")
                print(f"SSL version: {ssock.version()}")
                print(f"Cipher: {ssock.cipher()}")
                return True
    except Exception as e:
        print(f"❌ SSL connection failed: {str(e)}")
        
        # Try with a more permissive context
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.verify_mode = ssl.CERT_NONE
            context.check_hostname = False
            
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock) as ssock:
                    print(f"✅ SSL connection with permissive context successful")
                    return True
        except Exception as e2:
            print(f"❌ SSL connection with permissive context also failed: {str(e2)}")
    
    return False

def test_connection(connection_string, **kwargs):
    """Test a MongoDB connection with the given connection string and options."""
    print(f"\nTesting connection with: {connection_string}")
    print(f"Additional options: {kwargs}")
    
    try:
        # Create client with the connection string
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000, **kwargs)
        
        # Try to get server info
        server_info = client.admin.command('ping')
        print(f"✅ Connection successful!")
        print(f"Server ping response: {server_info}")
        
        # List databases
        try:
            databases = client.list_database_names()
            print(f"Available databases: {databases}")
            
            # Try to access the specific database
            db = client.get_database('Newpy')
            collections = db.list_collection_names()
            print(f"Collections in 'Newpy': {collections}")
        except Exception as e:
            print(f"⚠️ Could connect but had issues listing databases: {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def main():
    """Test multiple connection approaches with comprehensive diagnostics."""
    print("Improved MongoDB Connection Tester")
    print("=================================")
    
    # Print system information
    print_system_info()
    
    # Test DNS resolution for MongoDB Atlas hostnames
    test_dns_resolution('cluster0.01myarq.mongodb.net')
    test_dns_resolution('ac-uowy13k-shard-00-00.01myarq.mongodb.net')
    test_dns_resolution('ac-uowy13k-shard-00-01.01myarq.mongodb.net')
    test_dns_resolution('ac-uowy13k-shard-00-02.01myarq.mongodb.net')
    
    # Test direct SSL connections
    test_ssl_connection('ac-uowy13k-shard-00-00.01myarq.mongodb.net')
    
    # Connection strings to test
    connection_strings = [
        # Standard Atlas connection string
        'mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/Newpy?retryWrites=true&w=majority',
        
        # Direct connection with explicit hosts
        'mongodb://kavin88701:nR1Cc1SOsgRiXedQ@ac-uowy13k-shard-00-00.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-01.01myarq.mongodb.net:27017,ac-uowy13k-shard-00-02.01myarq.mongodb.net:27017/Newpy?ssl=true&replicaSet=atlas-ixvlnj-shard-0&authSource=admin&retryWrites=true&w=majority',
    ]
    
    # Connection options to test
    connection_options = [
        # With TLS CA file and permissive SSL settings
        {
            'tlsCAFile': certifi.where(),
            'tlsAllowInvalidCertificates': True,
            'ssl': True,
            'ssl_cert_reqs': ssl.CERT_NONE
        },
        
        # With longer timeouts and permissive SSL settings
        {
            'serverSelectionTimeoutMS': 30000,
            'connectTimeoutMS': 30000,
            'socketTimeoutMS': 30000,
            'tlsCAFile': certifi.where(),
            'tlsAllowInvalidCertificates': True,
            'ssl': True,
            'ssl_cert_reqs': ssl.CERT_NONE
        },
        
        # With minimal SSL settings
        {
            'ssl': True,
            'ssl_cert_reqs': ssl.CERT_NONE
        }
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
        print("\nRecommendations:")
        print("1. Install or update required packages:")
        print("   pip install --upgrade pymongo dnspython certifi pyOpenSSL")
        print("2. Check your MongoDB Atlas dashboard to ensure:")
        print("   - Your IP address is whitelisted")
        print("   - Your username and password are correct")
        print("   - Your cluster is active and not paused")
        print("3. Try using a VPN or different network")
        print("4. Check if your system's SSL/TLS configuration is up to date")
        print("5. Try using a different Python version")

if __name__ == "__main__":
    main()
