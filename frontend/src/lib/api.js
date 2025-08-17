import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Tasks API
export const tasksAPI = {
  // Get all tasks
  getTasks: (params = {}) => api.get('/tasks/', { params }),
  
  // Create new task
  createTask: (taskData) => api.post('/tasks/', taskData),
  
  // Update task
  updateTask: (id, taskData) => api.patch(`/tasks/${id}/`, taskData),
  
  // Delete task
  deleteTask: (id) => api.delete(`/tasks/${id}/`),
  
  // Get task statistics
  getStatistics: () => api.get('/tasks/statistics/'),
  
  // Get priority distribution
  getPriorityDistribution: () => api.get('/tasks/priority_distribution/'),
};

// Categories API
export const categoriesAPI = {
  getCategories: () => api.get('/categories/'),
  createCategory: (categoryData) => api.post('/categories/', categoryData),
  getPopularCategories: () => api.get('/categories/popular/'),
};

// Context API
export const contextAPI = {
  getContextEntries: (params = {}) => api.get('/context-entries/', { params }),
  deleteContextEntry: (id) =>
  api.delete('/context-entries/delete_context/', {
    data: { id }   
  }),
  createContextEntry: (contextData) => api.post('/context-entries/', contextData),
  bulkCreateContextEntries: (contextArray) => api.post('/context-entries/bulk_create/', contextArray),
};

// Tags API
export const tagsAPI = {
  getTags: () => api.get('/tags/'),
  getPopularTags: () => api.get('/tags/popular/'),
};

// AI API
export const aiAPI = {
  getTaskSuggestions: (suggestionData) => api.post('/ai/task-suggestions/', suggestionData),
  prioritizeTasks: (prioritizationData) => api.post('/ai/task-prioritization/', prioritizationData),
};

export default api;