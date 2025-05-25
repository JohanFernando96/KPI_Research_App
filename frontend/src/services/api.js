import axios from 'axios';

// Create an axios instance with default config
export const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
    timeout: 240000, // 4mins timeout
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        // Handle common errors
        if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx

            // Handle 401 Unauthorized - redirect to login
            if (error.response.status === 401) {
                // Clear token and redirect to login
                localStorage.removeItem('auth_token');

                // If in a browser environment, redirect
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
            }

            // Handle 403 Forbidden - show access denied
            if (error.response.status === 403) {
                console.error('Access denied:', error.response.data);
            }

            // Handle 404 Not Found
            if (error.response.status === 404) {
                console.error('Resource not found:', error.response.data);
            }

            // Handle 500 Server Error
            if (error.response.status >= 500) {
                console.error('Server error:', error.response.data);
            }
        } else if (error.request) {
            // The request was made but no response was received
            console.error('Network error:', error.request);
        } else {
            // Something happened in setting up the request that triggered an Error
            console.error('Request error:', error.message);
        }

        return Promise.reject(error);
    }
);