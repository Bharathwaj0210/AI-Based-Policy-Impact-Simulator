import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const getInsurancePolicies = () => api.get('/insurance/policies/');
export const getGovernmentPolicies = () => api.get('/government/policies/');

export default api;
