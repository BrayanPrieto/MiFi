import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../store/auth';

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { guestOnly: true }
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('../views/Register.vue'),
        meta: { guestOnly: true }
    },
    {
        path: '/',
        component: () => import('../views/layouts/AppLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue')
            },
            {
                path: 'transactions',
                name: 'Transactions',
                component: () => import('../views/Transactions.vue')
            },
            {
                path: 'accounts',
                name: 'Accounts',
                component: () => import('../views/Accounts.vue')
            },
            {
                path: 'goals',
                name: 'Goals',
                component: () => import('../views/Goals.vue')
            },
            {
                path: 'categories',
                name: 'Categories',
                component: () => import('../views/Categories.vue')
            },
            {
                path: 'recurrents',
                name: 'Recurrents',
                component: () => import('../views/Recurrents.vue')
            }
        ]
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

router.beforeEach(async (to, _from, next) => {
    const authStore = useAuthStore();

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next({ name: 'Login' });
    } else if (to.meta.guestOnly && authStore.isAuthenticated) {
        next({ name: 'Dashboard' });
    } else {
        next();
    }
});

export default router;
