"""
Test script to verify bidding functionality.
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_bidding():
    """Test the bidding functionality."""
    print("\n=== Testing Bidding Functionality ===")
    
    # First, login to get a token
    print("\n1. Logging in...")
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            print(f"✅ Login successful! Token: {token[:20]}...")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login exception: {str(e)}")
        return
    
    # Get all items
    print("\n2. Getting all items...")
    try:
        response = requests.get(f"{BASE_URL}/items")
        print(f"Items Status Code: {response.status_code}")
        
        if response.status_code == 200:
            items = response.json()
            print(f"✅ Found {len(items)} items")
            
            if items:
                first_item = items[0]
                item_id = first_item['id']
                print(f"First item: {first_item['name']} - ${first_item['current_price']}")
                print(f"Item ID: {item_id}")
            else:
                print("❌ No items found")
                return
        else:
            print(f"❌ Failed to get items: {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception getting items: {str(e)}")
        return
    
    # Get current bids for the item
    print(f"\n3. Getting current bids for item {item_id}...")
    try:
        response = requests.get(f"{BASE_URL}/items/{item_id}/bids")
        print(f"Bids Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bids = response.json()
            print(f"✅ Found {len(bids)} existing bids")
            for i, bid in enumerate(bids[:3]):  # Show first 3 bids
                print(f"  Bid {i+1}: ${bid['amount']} at {bid['timestamp']}")
        else:
            print(f"❌ Failed to get bids: {response.text}")
    except Exception as e:
        print(f"❌ Exception getting bids: {str(e)}")
    
    # Place a bid
    print(f"\n4. Placing a bid on item {item_id}...")
    current_price = first_item['current_price']
    bid_amount = current_price + 10.0  # Bid $10 more than current price
    
    bid_data = {
        "amount": bid_amount
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/items/{item_id}/bid", 
                               json=bid_data, 
                               headers=headers)
        print(f"Bid Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bid placed successfully!")
            print(f"Bid ID: {result.get('bid_id')}")
            print(f"Bid Amount: ${bid_amount}")
        else:
            print(f"❌ Failed to place bid: {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception placing bid: {str(e)}")
        return
    
    # Get updated bids
    print(f"\n5. Getting updated bids for item {item_id}...")
    try:
        response = requests.get(f"{BASE_URL}/items/{item_id}/bids")
        print(f"Updated Bids Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bids = response.json()
            print(f"✅ Found {len(bids)} bids after placing new bid")
            for i, bid in enumerate(bids[:3]):  # Show first 3 bids
                print(f"  Bid {i+1}: ${bid['amount']} at {bid['timestamp']}")
        else:
            print(f"❌ Failed to get updated bids: {response.text}")
    except Exception as e:
        print(f"❌ Exception getting updated bids: {str(e)}")
    
    # Get updated item to check price
    print(f"\n6. Getting updated item to check price...")
    try:
        response = requests.get(f"{BASE_URL}/items/{item_id}")
        print(f"Updated Item Status Code: {response.status_code}")
        
        if response.status_code == 200:
            item = response.json()
            print(f"✅ Item current price: ${item['current_price']}")
            if item['current_price'] == bid_amount:
                print("✅ Item price updated correctly!")
            else:
                print(f"❌ Item price not updated correctly. Expected: ${bid_amount}, Got: ${item['current_price']}")
        else:
            print(f"❌ Failed to get updated item: {response.text}")
    except Exception as e:
        print(f"❌ Exception getting updated item: {str(e)}")

if __name__ == "__main__":
    test_bidding()
