import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// MCP Layer APIs
export const searchContext = async (query, topK = 3) => {
  const response = await axios.get(`${API}/mcp/search`, {
    params: { q: query, top_k: topK }
  });
  return response.data;
};

export const getConnections = async (query, topK = 2, depth = 1) => {
  const response = await axios.get(`${API}/mcp/connections`, {
    params: { q: query, top_k: topK, depth }
  });
  return response.data;
};

// Application Layer APIs
export const getContext = async (query, topK = 3) => {
  const response = await axios.get(`${API}/context`, {
    params: { query, top_k: topK }
  });
  return response.data;
};

export const getIncidentReport = async (query) => {
  const response = await axios.get(`${API}/incident`, {
    params: { query }
  });
  return response.data;
};

export const getRoleTask = async (role, query) => {
  const response = await axios.get(`${API}/role/${role}/task`, {
    params: { query }
  });
  return response.data;
};

export default {
  searchContext,
  getConnections,
  getContext,
  getIncidentReport,
  getRoleTask
};
