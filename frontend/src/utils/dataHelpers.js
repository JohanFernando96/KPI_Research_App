/**
 * Safely extract ID from an object or return the value if it's already a string
 * @param {Object|string} item - The item to extract ID from
 * @returns {string|null} - The extracted ID or null if not found
 */
export const extractId = (item) => {
  if (!item) return null;
  
  // If it's already a string, return it
  if (typeof item === 'string') {
    // Check if it's a valid MongoDB ObjectId format (24 hex characters)
    if (/^[0-9a-fA-F]{24}$/.test(item)) {
      return item;
    }
    // If it's '[object Object]' or other invalid format, return null
    if (item === '[object Object]' || item.includes('[object')) {
      console.error('Invalid ID format detected:', item);
      return null;
    }
    return item;
  }
  
  // If it's an object, try to extract the ID
  if (typeof item === 'object' && item !== null) {
    // Check for _id first (MongoDB), then id
    const id = item._id || item.id;
    
    // Handle MongoDB ObjectId objects
    if (id && typeof id === 'object' && id.$oid) {
      return id.$oid;
    }
    
    return id || null;
  }
  
  return null;
};

/**
 * Safely extract employee data ensuring IDs are strings
 * @param {Object} employee - The employee object
 * @returns {Object} - The employee object with string ID
 */
export const normalizeEmployee = (employee) => {
  if (!employee) return null;
  
  const id = extractId(employee);
  
  if (!id) {
    console.warn('Employee without valid ID:', employee);
  }
  
  return {
    ...employee,
    _id: id,
    id: id // Some components might use 'id' instead of '_id'
  };
};

/**
 * Check if a value is a valid MongoDB ObjectId
 * @param {string} id - The ID to check
 * @returns {boolean} - True if valid ObjectId format
 */
export const isValidObjectId = (id) => {
  if (!id || typeof id !== 'string') return false;
  return /^[0-9a-fA-F]{24}$/.test(id);
};