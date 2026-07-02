import axios from 'axios';
import { useAuthStore } from '../store/auth';

// En dev (pnpm dev) el backend corre en localhost:8000; en Docker, nginx proxyea /api al backend
const baseURL = import.meta.env.VITE_API_URL
    || (import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1');

export const apiClient = axios.create({
    baseURL,
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
