"""Utility functions with duplicate code."""

import json
import requests


def process_user_data(user_id):
    """Process user data."""
    # Fetch data
    response = requests.get(f"https://api.example.com/users/{user_id}")
    data = response.json()
    
    # Validate data
    if 'name' not in data:
        return None
    if 'email' not in data:
        return None
    if 'age' not in data:
        return None
    
    # Process data
    result = {
        'name': data['name'].upper(),
        'email': data['email'].lower(),
        'age': int(data['age'])
    }
    
    return result


def process_product_data(product_id):
    """Process product data."""
    # Fetch data
    response = requests.get(f"https://api.example.com/products/{product_id}")
    data = response.json()
    
    # Validate data
    if 'name' not in data:
        return None
    if 'price' not in data:
        return None
    if 'stock' not in data:
        return None
    
    # Process data
    result = {
        'name': data['name'].upper(),
        'price': float(data['price']),
        'stock': int(data['stock'])
    }
    
    return result


def unused_utility():
    """Never used anywhere."""
    return "helper"

