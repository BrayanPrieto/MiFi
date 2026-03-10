import { createApp } from "vue";
import App from "./App.vue";
import { createPinia } from "pinia";
import router from "./router";

import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import ConfirmationService from 'primevue/confirmationservice';
import ToastService from 'primevue/toastservice';
import 'primeicons/primeicons.css';
import './style.css'; // Global CSS

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            prefix: 'p',
            darkModeSelector: 'none',
            cssLayer: false
        }
    }
});
app.use(ConfirmationService);
app.use(ToastService);

// Cargar usuario al inicio si hay token guardado
import { useAuthStore } from './store/auth';
const authStore = useAuthStore();
if (authStore.token) {
    authStore.fetchUser();
}

app.mount("#app");
