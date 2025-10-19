// Test JavaScript file with slop

import { helper } from './utils';

// TODO: Add proper validation
// FIXME: This is a temporary hack

/**
 * calculateTotal calculates the total
 */
function calculateTotal(items) {
    // Initialize total
    let total = 0;
    
    // Loop through items
    for (let item of items) {
        // Add to total
        total += item;
    }
    
    // Return result
    return total;
}

// Legacy code - for backwards compatibility
function legacyFunction() {
    return "old";
}

// function oldImplementation() {
//     return "deprecated";
// }

function unusedHelper() {
    return 42;
}

function deeplyNested(data) {
    if (data) {
        if (Array.isArray(data)) {
            if (data.length > 0) {
                if (data[0] !== null) {
                    if (typeof data[0] === 'object') {
                        if ('key' in data[0]) {
                            return data[0].key;
                        }
                    }
                }
            }
        }
    }
    return null;
}

function functionWithEmptyCatch() {
    try {
        riskyOperation();
    } catch (error) {
        // Empty catch block
    }
}

function riskyOperation() {
    throw new Error("Something went wrong");
}

// Duplicate validation code
function validateUser(user) {
    if (!user.name) {
        return false;
    }
    if (!user.email) {
        return false;
    }
    if (!user.age) {
        return false;
    }
    return true;
}

function validateProduct(product) {
    if (!product.name) {
        return false;
    }
    if (!product.price) {
        return false;
    }
    if (!product.stock) {
        return false;
    }
    return true;
}

export { calculateTotal, legacyFunction, validateUser };

