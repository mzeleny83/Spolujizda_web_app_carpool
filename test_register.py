import requests
import json

# Test registrace
data = {
    "name": "Test User",
    "phone": "+420123456789",
    "email": "test@example.com",
    "password": "testpassword",
    "password_confirm": "testpassword"
}

try:
    response = requests.post("http://localhost:5000/api/users/register", 
                           json=data, 
                           headers={"Content-Type": "application/json"})
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")