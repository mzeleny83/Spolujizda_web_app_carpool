#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://spolujizda-645ec54e47aa.herokuapp.com"

def check_users():
    print("Checking existing users...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/list")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users:")
            for user in users[:10]:  # Show first 10 users
                print(f"  - ID: {user['id']}, Name: {user['name']}, Phone: {user['phone']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def check_rides():
    print("\nChecking existing rides...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/rides/all")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            rides = response.json()
            print(f"Found {len(rides)} rides:")
            for ride in rides[:5]:  # Show first 5 rides
                print(f"  - ID: {ride['id']}, Driver: {ride['driver_name']}, From: {ride['from_location']} To: {ride['to_location']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()
    check_rides()