import axios from 'axios';
import { useAuthStore } from '../store/auth';

export const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use((config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // Manejo global de errores y sesión expirada
        if (error.response?.status === 401 || error.response?.status === 403) {
            const authStore = useAuthStore();
            authStore.logout();
        }
        return Promise.reject(error);
    }
);
