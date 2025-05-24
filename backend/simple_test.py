"""
Simple test to check basic API functionality.
"""
import requests

def test_basic_endpoints():
    """Test basic endpoints."""
    base_url = "http://localhost:5000"
    
    print("Testing basic endpoints...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code} - {response.text[:50]}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test items endpoint
    try:
        response = requests.get(f"{base_url}/api/items")
        print(f"Items endpoint: {response.status_code}")
        if response.status_code == 200:
            items = response.json()
            print(f"Found {len(items)} items")
            if items:
                print(f"First item: {items[0]['name']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Items endpoint error: {e}")

if __name__ == "__main__":
    test_basic_endpoints()
