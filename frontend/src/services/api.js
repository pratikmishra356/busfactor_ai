import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// MCP Layer APIs
export const searchContext = async (query, topK = 3) => {
  const response = await api.get('/api/mcp/search', {
    params: { q: query, top_k: topK },
  });
  return response.data;
};

export const getConnections = async (query, topK = 2, depth = 1) => {
  const response = await api.get('/api/mcp/connections', {
    params: { q: query, top_k: topK, depth },
  });
  return response.data;
};

export const getEntityDetails = async (entityId) => {
  const response = await api.get(`/api/mcp/entity/${entityId}`);
  return response.data;
};

// Code Audit APIs
export const codeAuditByFilePath = async (filePath, limit = 10) => {
  const response = await api.get('/api/code/audit', {
    params: { file_path: filePath, limit },
  });
  return response.data;
};

export const codeAuditByComment = async (comment, limit = 10) => {
  const response = await api.get('/api/code/audit', {
    params: { comment, limit },
  });
  return response.data;
};

export const codeAuditByQuery = async (query, limit = 10) => {
  const response = await api.get('/api/code/audit', {
    params: { query, limit },
  });
  return response.data;
};

// Application Layer APIs
export const getContextResponse = async (query, topK = 3) => {
  const response = await api.get('/api/context', {
    params: { query, top_k: topK },
  });
  return response.data;
};

export const getIncidentReport = async (query) => {
  const response = await api.get('/api/incident', {
    params: { query },
  });
  return response.data;
};

export const getRoleTask = async (role, query) => {
  const response = await api.get(`/api/role/${role}/task`, {
    params: { query },
  });
  return response.data;
};

export default api;
