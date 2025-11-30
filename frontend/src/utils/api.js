import axios from 'axios';

// Get API URL from environment variable or use relative path for development
// In production (Vercel), set VITE_API_URL to your Railway backend URL
// Example: VITE_API_URL=https://your-app.railway.app
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

