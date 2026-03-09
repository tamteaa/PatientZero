import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const client = axios.create({
  baseURL: API_BASE,
});

export { API_BASE };
