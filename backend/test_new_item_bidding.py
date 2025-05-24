"""
Test bidding on the newly created active auction item.
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"
NEW_ITEM_ID = "683199c267b378733f1b81ad"  # The newly created item

def test_new_item_bidding():
    """Test bidding on the new active auction item."""
    print(f"\n=== Testing Bidding on New Item {NEW_ITEM_ID} ===")
    
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
            print(f"✅ Login successful!")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login exception: {str(e)}")
        return
    
    # Get the specific item details
    print(f"\n2. Getting item details for {NEW_ITEM_ID}...")
    try:
        response = requests.get(f"{BASE_URL}/items/{NEW_ITEM_ID}")
        print(f"Item Status Code: {response.status_code}")
        
        if response.status_code == 200:
            item = response.json()
            print(f"✅ Item found: {item['name']}")
            print(f"   Current Price: ${item['current_price']}")
            print(f"   Status: {item['status']}")
            print(f"   End Time: {item['end_time']}")
        else:
            print(f"❌ Failed to get item: {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception getting item: {str(e)}")
        return
    
    # Get current bids for the new item
    print(f"\n3. Getting current bids for new item...")
    try:
        response = requests.get(f"{BASE_URL}/items/{NEW_ITEM_ID}/bids")
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
    
    # Place a bid on the new item
    print(f"\n4. Placing a bid on new item...")
    current_price = item['current_price']
    bid_amount = current_price + 25.0  # Bid $25 more than current price
    
    bid_data = {
        "amount": bid_amount
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/items/{NEW_ITEM_ID}/bid", 
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
    
    # Get updated bids to verify the bid was added
    print(f"\n5. Getting updated bids to verify...")
    try:
        response = requests.get(f"{BASE_URL}/items/{NEW_ITEM_ID}/bids")
        print(f"Updated Bids Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bids = response.json()
            print(f"✅ Found {len(bids)} bids after placing new bid")
            for i, bid in enumerate(bids[:3]):  # Show first 3 bids
                print(f"  Bid {i+1}: ${bid['amount']} at {bid['timestamp']}")
                
            # Check if our bid is there
            our_bid = next((bid for bid in bids if bid['amount'] == bid_amount), None)
            if our_bid:
                print(f"✅ Our bid of ${bid_amount} is visible in the bid list!")
            else:
                print(f"❌ Our bid of ${bid_amount} is not visible in the bid list")
        else:
            print(f"❌ Failed to get updated bids: {response.text}")
    except Exception as e:
        print(f"❌ Exception getting updated bids: {str(e)}")
    
    # Get updated item to check if price was updated
    print(f"\n6. Getting updated item to check price...")
    try:
        response = requests.get(f"{BASE_URL}/items/{NEW_ITEM_ID}")
        print(f"Updated Item Status Code: {response.status_code}")
        
        if response.status_code == 200:
            updated_item = response.json()
            print(f"✅ Updated item current price: ${updated_item['current_price']}")
            if updated_item['current_price'] == bid_amount:
                print("✅ Item price updated correctly!")
            else:
                print(f"❌ Item price not updated. Expected: ${bid_amount}, Got: ${updated_item['current_price']}")
        else:
            print(f"❌ Failed to get updated item: {response.text}")
    except Exception as e:
        print(f"❌ Exception getting updated item: {str(e)}")

if __name__ == "__main__":
    test_new_item_bidding()
