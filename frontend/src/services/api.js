import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});


// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
// Auth API
export const authAPI = {
  register: (data) => api.post('/register', data),
  login: (data) => api.post('/login', new URLSearchParams(data), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
  getMe: () => api.get('/me'),
  forgotPassword: (email) => api.post('/forgot-password', { email }),
  resetPassword: (data) => api.post('/reset-password', data),
};

// Expense API
export const expenseAPI = {
  create: (data) => api.post('/expenses', data),
  getAll: (params) => api.get('/expenses', { params }),
  getById: (id) => api.get(`/expenses/${id}`),
  update: (id, data) => api.put(`/expenses/${id}`, data),
  delete: (id) => api.delete(`/expenses/${id}`),
  getSummary: () => api.get('/dashboard/summary'),
  getMonthlyStats: () => api.get('/dashboard/monthly-stats'),
};

// Income API
export const incomeAPI = {
  create: (data) => api.post('/income', data),
  getAll: () => api.get('/income'),
  update: (id, data) => api.put(`/income/${id}`, data),
  delete: (id) => api.delete(`/income/${id}`),
};

// Financial API
export const financialAPI = {
  getOverview: () => api.get('/financial-overview'),
  getRecommendations: () => api.get('/recommendations'),
  getBudgetSuggestions: () => api.get('/budget-suggestions'),
};
// Chat API
export const chatAPI = {
  sendMessage: (message) => api.post('/chat', { message }),
};
export default api;