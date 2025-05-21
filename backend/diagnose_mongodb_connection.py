"""
Diagnostic script for MongoDB Atlas connection issues.
This script performs various tests to diagnose MongoDB Atlas connectivity problems.
"""
import sys
import socket
import ssl
import dns.resolver
import certifi
import platform
import subprocess
import os
from pymongo import MongoClient
from urllib.parse import urlparse

def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def print_info(label, value):
    """Print an info line."""
    print(f"{label.ljust(25)}: {value}")

def check_system_info():
    """Check system information."""
    print_section("System Information")
    print_info("Platform", platform.platform())
    print_info("Python Version", platform.python_version())
    print_info("Architecture", platform.architecture()[0])
    
    # Check SSL version
    print_info("OpenSSL Version", ssl.OPENSSL_VERSION)
    
    # Check if running in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    print_info("Virtual Environment", "Yes" if in_venv else "No")

def check_dns_resolution(hostname):
    """Check DNS resolution for a hostname."""
    print_section(f"DNS Resolution for {hostname}")
    
    try:
        # Try standard DNS resolution
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        print_info("IP Addresses", ", ".join(ip_addresses))
        return True
    except socket.gaierror as e:
        print_info("DNS Resolution Error", str(e))
        return False

def check_connectivity(hostname, port=27017):
    """Check TCP connectivity to a host and port."""
    print_section(f"TCP Connectivity to {hostname}:{port}")
    
    try:
        # Create a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        # Try to connect
        result = sock.connect_ex((hostname, port))
        if result == 0:
            print_info("Connection Status", "Success")
            return True
        else:
            print_info("Connection Status", f"Failed (Error code: {result})")
            return False
    except socket.error as e:
        print_info("Connection Error", str(e))
        return False
    finally:
        sock.close()

def ping_host(hostname):
    """Ping a hostname to check basic connectivity."""
    print_section(f"Ping Test for {hostname}")
    
    # Determine the ping command based on the OS
    ping_cmd = "ping"
    ping_args = ["-n", "4"] if platform.system().lower() == "windows" else ["-c", "4"]
    
    try:
        # Run the ping command
        result = subprocess.run([ping_cmd, *ping_args, hostname], 
                               capture_output=True, text=True, timeout=10)
        
        # Print the output
        print(result.stdout)
        
        return result.returncode == 0
    except subprocess.SubprocessError as e:
        print_info("Ping Error", str(e))
        return False

def test_ssl_handshake(hostname, port=27017):
    """Test SSL handshake with a host."""
    print_section(f"SSL Handshake Test for {hostname}:{port}")
    
    try:
        # Create a standard socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        # Connect to the host
        sock.connect((hostname, port))
        
        # Wrap with SSL
        context = ssl.create_default_context(cafile=certifi.where())
        ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
        
        # Get the certificate
        cert = ssl_sock.getpeercert()
        
        print_info("SSL Handshake", "Success")
        print_info("Certificate Subject", cert.get('subject', 'Unknown'))
        print_info("Certificate Issuer", cert.get('issuer', 'Unknown'))
        
        return True
    except ssl.SSLError as e:
        print_info("SSL Error", str(e))
        return False
    except socket.error as e:
        print_info("Socket Error", str(e))
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def parse_connection_string(connection_string):
    """Parse a MongoDB connection string to extract hosts."""
    if connection_string.startswith('mongodb+srv://'):
        # For SRV connection strings, extract the hostname
        parts = connection_string.split('@')
        if len(parts) > 1:
            hostname = parts[1].split('/')[0]
            return [hostname]
    elif connection_string.startswith('mongodb://'):
        # For standard connection strings, extract all hosts
        parts = connection_string.split('@')
        if len(parts) > 1:
            hosts_part = parts[1].split('/')[0]
            return hosts_part.split(',')
    
    return []

def main():
    """Main diagnostic function."""
    print_section("MongoDB Atlas Connection Diagnostics")
    
    # Connection string to test
    connection_string = 'mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/Newpy?retryWrites=true&w=majority'
    print_info("Connection String", connection_string)
    
    # Check system information
    check_system_info()
    
    # Parse the connection string to get hosts
    hosts = parse_connection_string(connection_string)
    if not hosts:
        print("Failed to parse connection string for hosts.")
        return
    
    # For each host, perform connectivity tests
    for host in hosts:
        # Check DNS resolution
        if check_dns_resolution(host):
            # Ping the host
            ping_host(host)
            
            # Check TCP connectivity
            if check_connectivity(host):
                # Test SSL handshake
                test_ssl_handshake(host)
    
    # Try to connect to MongoDB Atlas
    print_section("MongoDB Connection Test")
    try:
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            tlsCAFile=certifi.where()
        )
        
        # Try to get server info
        server_info = client.server_info()
        print_info("Connection Status", "Success")
        print_info("Server Version", server_info.get('version', 'Unknown'))
        
        # List databases
        databases = client.list_database_names()
        print_info("Available Databases", ", ".join(databases))
    except Exception as e:
        print_info("Connection Error", str(e))
    
    print_section("Recommendations")
    print("""
1. Check your MongoDB Atlas dashboard to ensure the cluster is running
2. Verify that your IP address is whitelisted in MongoDB Atlas
3. Check if your network allows outbound connections to MongoDB Atlas
4. Try updating your Python, pymongo, and certifi packages
5. Try connecting from a different network
6. For development, consider using a local MongoDB instance
""")

if __name__ == "__main__":
    main()
