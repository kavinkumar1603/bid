"""
Check your public IP address and provide instructions for whitelisting it in MongoDB Atlas.
"""
import requests
import socket
import json

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Create a socket connection to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {str(e)}")
        return "Unknown"

def get_public_ip():
    """Get the public IP address of the machine."""
    try:
        # Use a public API to get the public IP
        response = requests.get("https://api.ipify.org?format=json")
        if response.status_code == 200:
            data = response.json()
            return data.get("ip")
        else:
            print(f"Error getting public IP: HTTP {response.status_code}")
            return "Unknown"
    except Exception as e:
        print(f"Error getting public IP: {str(e)}")
        return "Unknown"

def main():
    """Main function to check IP addresses."""
    print("IP Address Checker for MongoDB Atlas")
    print("===================================")
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"Local IP address: {local_ip}")
    
    # Get public IP
    public_ip = get_public_ip()
    print(f"Public IP address: {public_ip}")
    
    print("\nInstructions for whitelisting your IP in MongoDB Atlas:")
    print("1. Log in to your MongoDB Atlas account at https://cloud.mongodb.com")
    print("2. Select your project and cluster")
    print("3. Click on 'Network Access' in the left sidebar")
    print("4. Click the '+ ADD IP ADDRESS' button")
    print(f"5. Enter your public IP address: {public_ip}")
    print("6. Optionally, add a description like 'My development machine'")
    print("7. Click 'Confirm'")
    print("\nAlternatively, you can allow access from anywhere (not recommended for production):")
    print("1. Click the '+ ADD IP ADDRESS' button")
    print("2. Click 'ALLOW ACCESS FROM ANYWHERE'")
    print("3. Click 'Confirm'")

if __name__ == "__main__":
    main()
