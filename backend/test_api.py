"""
Test script to verify API endpoints are working correctly.
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_get_items():
    """Test getting all items."""
    print("\n=== Testing GET /api/items ===")
    try:
        response = requests.get(f"{BASE_URL}/items")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            items = response.json()
            print(f"✅ Found {len(items)} items")
            for i, item in enumerate(items[:3]):  # Show first 3 items
                print(f"  {i+1}. {item['name']} - ${item['current_price']}")
            return items
        else:
            print(f"❌ Error: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return []

def test_get_item(item_id):
    """Test getting a specific item."""
    print(f"\n=== Testing GET /api/items/{item_id} ===")
    try:
        response = requests.get(f"{BASE_URL}/items/{item_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            item = response.json()
            print(f"✅ Item found: {item['name']}")
            print(f"   Description: {item['description'][:50]}...")
            print(f"   Price: ${item['current_price']}")
            print(f"   Category: {item['category']}")
            return item
        else:
            print(f"❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def test_get_item_bids(item_id):
    """Test getting bids for a specific item."""
    print(f"\n=== Testing GET /api/items/{item_id}/bids ===")
    try:
        response = requests.get(f"{BASE_URL}/items/{item_id}/bids")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bids = response.json()
            print(f"✅ Found {len(bids)} bids for this item")
            for i, bid in enumerate(bids[:3]):  # Show first 3 bids
                print(f"  {i+1}. ${bid['amount']} at {bid['timestamp']}")
            return bids
        else:
            print(f"❌ Error: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return []

def test_login():
    """Test user login."""
    print("\n=== Testing POST /api/login ===")
    try:
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful for user: {data['user']['username']}")
            print(f"   User type: {data['user']['user_type']}")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def main():
    """Run all API tests."""
    print("🚀 Starting API Tests...")
    
    # Test getting all items
    items = test_get_items()
    
    if items:
        # Test getting a specific item
        first_item = items[0]
        item_id = first_item['id']
        test_get_item(item_id)
        
        # Test getting bids for the item
        test_get_item_bids(item_id)
    
    # Test login
    token = test_login()
    
    print("\n🎉 API Tests completed!")
    
    if items and token:
        print("\n✅ All basic API endpoints are working correctly!")
        print("✅ You can now test the frontend application.")
        print("\n📝 Test credentials:")
        print("   Username: testuser")
        print("   Password: password123")
        print("\n🌐 Frontend URL: http://localhost:3001")
        print("🔧 Backend URL: http://localhost:5000")
    else:
        print("\n❌ Some API endpoints are not working correctly.")

if __name__ == "__main__":
    main()
