import axios from 'axios';

// Use environment variable for production, fallback to localhost for development
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const API_BASE = API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`;

export const uploadDataset = async (domain, file, extraData = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.keys(extraData).forEach(key => formData.append(key, extraData[key]));

    const response = await axios.post(`${API_BASE}/${domain}/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const filterDataset = async (domain, data, filters, extraData = {}) => {
    const payload = { data, filters, ...extraData };
    const response = await axios.post(`${API_BASE}/${domain}/filter/`, payload);
    return response.data;
};

export const explainModel = async (domain, data, filters, extraData = {}) => {
    const payload = { data, filters, ...extraData };
    const response = await axios.post(`${API_BASE}/${domain}/explain/`, payload);
    return response.data;
};

export const getGeminiSummary = async (domain, extraData = {}) => {
    const response = await axios.post(`${API_BASE}/${domain}/gemini-summary/`, extraData);
    return response.data;
};
