import { defineStore } from 'pinia';
import { apiClient } from '../api/client';

interface User {
    id: string;
    nombre: string;
    email: string;
    moneda: string;
}

interface AuthState {
    token: string | null;
    user: User | null;
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthState => ({
        token: localStorage.getItem('token') || null,
        user: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
    },
    actions: {
        async login(payload: Record<string, any>) {
            const data = new URLSearchParams();
            data.append('username', payload.email);
            data.append('password', payload.password);

            const response = await apiClient.post('/auth/login/access-token', data, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            this.token = response.data.access_token;
            localStorage.setItem('token', this.token as string);
            await this.fetchUser();
        },
        async fetchUser() {
            if (!this.token) return;
            try {
                const response = await apiClient.get('/usuarios/me');
                this.user = response.data;
            } catch (error) {
                this.logout();
            }
        },
        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('token');
            // Redirigir será manejado por el guardia de rutas o componente
        }
    }
});
