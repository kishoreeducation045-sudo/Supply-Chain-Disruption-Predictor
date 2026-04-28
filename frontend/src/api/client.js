import axios from 'axios';
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const api = axios.create({ baseURL });
export const getNetwork = () => api.get('/network');
export const runSimulation = (text) => api.post('/simulate', { scenario_text: text });
export const getMitigation = (id) => api.post('/mitigate', { failing_node_id: id });