<template>
  <div class="h-screen w-screen flex items-center justify-center p-6">
    <div class="w-full max-w-md p-8 glass-strong soft-enter">

      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center mb-4 relative">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-mifi-navy to-mifi-navy-light flex items-center justify-center transform rotate-3 shadow-soft-lg ring-1 ring-mifi-cyan/40">
                <i class="pi pi-chart-line text-mifi-green text-3xl"></i>
            </div>
        </div>
        <h1 class="text-4xl font-extrabold font-display text-mifi-navy tracking-tight mb-1">
            M<span class="text-mifi-cyan">i</span>F<span class="text-mifi-green">i</span>
        </h1>
        <p class="eyebrow mt-2">Estabilidad financiera</p>
      </div>

      <Message v-if="errorMsg" severity="error" :closable="false" class="mb-4">{{ errorMsg }}</Message>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
            <label for="email" class="font-medium text-surface-900 dark:text-surface-0">Correo Electrónico</label>
            <InputText id="email" v-model="email" type="email" placeholder="ejemplo@correo.com" required class="w-full bg-surface-50 border-surface-200 text-mifi-navy placeholder:text-surface-400 focus:border-mifi-cyan" />
        </div>
        
        <div class="flex flex-col gap-2">
            <label for="password" class="font-medium text-surface-900 dark:text-surface-0">Contraseña</label>
            <Password id="password" v-model="password" :feedback="false" toggleMask required inputClass="w-full bg-surface-50 border-surface-200 text-mifi-navy placeholder:text-surface-400 focus:border-mifi-cyan" class="w-full" />
        </div>

        <Button type="submit" label="Iniciar Sesión" icon="pi pi-sign-in" :loading="loading" class="w-full mt-4 !bg-mifi-cyan hover:!bg-mifi-cyan/80 !border-none !text-white" size="large" />
      </form>

      <div class="mt-6 text-center text-sm text-surface-600 dark:text-surface-400">
        ¿No tienes cuenta? <router-link to="/register" class="text-mifi-cyan hover:underline font-medium">Regístrate aquí</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';

import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';
import Message from 'primevue/message';

const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMsg = ref('');

const authStore = useAuthStore();
const router = useRouter();

const handleLogin = async () => {
    loading.value = true;
    errorMsg.value = '';
    
    try {
        await authStore.login({ email: email.value, password: password.value });
        router.push('/');
    } catch (err: any) {
        errorMsg.value = err.response?.data?.detail || 'Error al iniciar sesión. Verifica tus credenciales.';
    } finally {
        loading.value = false;
    }
};
</script>
