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

// Agent APIs
export const runCodeHealthAgent = async (prInput) => {
  const response = await api.post('/api/agent/codehealth', prInput);
  return response.data;
};

export const runEmployeeAgent = async (role, task) => {
  const response = await api.post('/api/agent/employee', { role, task });
  return response.data;
};

// Application Layer APIs (deprecated - use agents instead)
export const getContextResponse = async (query, topK = 3) => {
  // Deprecated
  throw new Error('Use runCodeHealthAgent instead');
};

export const getIncidentReport = async (query) => {
  // Deprecated - will be replaced by OnCall Agent
  throw new Error('Use OnCall Agent instead (coming soon)');
};

export const getRoleTask = async (role, query) => {
  // Deprecated - will be replaced by Employee Agent
  throw new Error('Use Employee Agent instead (coming soon)');
};

export default api;
