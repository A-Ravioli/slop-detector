"""Test application with intentional slop."""

import os
import sys
from typing import List

# TODO: Implement proper error handling
# FIXME: This is a hack


def calculate_total(items: List[int]) -> int:
    """Calculate total.
    
    This function calculates the total of items.
    """
    # Initialize total to zero
    total = 0
    
    # Loop through items
    for item in items:
        # Add item to total
        total += item
    
    # Return the total
    return total


def legacy_function():
    """This is for backwards compatibility. Don't use in new code."""
    pass


# def old_implementation():
#     """Old way of doing things."""
#     return "deprecated"


def unused_helper():
    """This function is never called anywhere."""
    return 42


def deeply_nested_function(data):
    """Function with deep nesting."""
    if data:
        if isinstance(data, list):
            if len(data) > 0:
                if data[0] is not None:
                    if isinstance(data[0], dict):
                        if 'key' in data[0]:
                            return data[0]['key']
    return None


def very_long_function_with_many_lines():
    """This function is way too long."""
    result = []
    
    for i in range(100):
        if i % 2 == 0:
            result.append(i)
        else:
            result.append(i * 2)
    
    for i in range(100):
        if i % 3 == 0:
            result.append(i)
        else:
            result.append(i * 3)
    
    for i in range(100):
        if i % 4 == 0:
            result.append(i)
        else:
            result.append(i * 4)
    
    for i in range(100):
        if i % 5 == 0:
            result.append(i)
        else:
            result.append(i * 5)
    
    for i in range(100):
        if i % 6 == 0:
            result.append(i)
        else:
            result.append(i * 6)
    
    for i in range(100):
        if i % 7 == 0:
            result.append(i)
        else:
            result.append(i * 7)
    
    return result


def function_with_empty_except():
    """Bad error handling."""
    try:
        risky_operation()
    except:
        pass


def function_with_generic_except():
    """Generic exception handling."""
    try:
        another_risky_operation()
    except Exception:
        return None


def risky_operation():
    """Placeholder."""
    pass


def another_risky_operation():
    """Placeholder."""
    pass

