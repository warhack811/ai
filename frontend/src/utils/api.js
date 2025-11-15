// src/utils/api.js

import axios from 'axios';
import { API_BASE_URL } from './constants';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

// Basit interceptor (log için)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API error:', error);
    throw error;
  }
);
