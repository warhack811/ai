/**
 * documentsApi.js - FAS 3
 * -----------------------
 * Document upload API helper functions
 */

import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const documentsApi = {
  /**
   * Upload document (text content)
   */
  uploadDocument: async (filename, content, metadata = {}) => {
    const response = await axios.post(`${API_URL}/upload-document`, {
      filename,
      content,
      metadata,
    });
    return response.data;
  },

  /**
   * List all documents
   */
  listDocuments: async (userId = 'default') => {
    const response = await axios.get(`${API_URL}/documents`, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * Delete document
   */
  deleteDocument: async (docId) => {
    const response = await axios.delete(`${API_URL}/documents/${docId}`);
    return response.data;
  },

  /**
   * Get knowledge base stats
   */
  getKnowledgeStats: async () => {
    const response = await axios.get(`${API_URL}/knowledge/stats`);
    return response.data;
  },
};

export default documentsApi;