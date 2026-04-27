import axios from 'axios';

const BACKEND_URL = 'http://localhost:8000/api/v1';

export const getNetwork = async () => {
  const response = await axios.get(`${BACKEND_URL}/network`);
  return response.data;
};

export const runSimulation = async (scenario_text) => {
  const response = await axios.post(`${BACKEND_URL}/simulate`, { scenario_text });
  return response.data;
};

export const getMitigation = async (failing_node_id) => {
  const response = await axios.post(`${BACKEND_URL}/mitigate`, { failing_node_id });
  return response.data;
};
