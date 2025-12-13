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
