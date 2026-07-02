<template>
  <div class="layout-wrapper flex flex-col h-screen w-screen overflow-hidden">
    <!-- Top Navigation Bar (Liquid Glass) -->
    <nav class="glass-strong flex items-center justify-between px-6 py-3 m-3 mb-0 z-50">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2 no-underline">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-mifi-cyan to-mifi-green flex items-center justify-center shadow-sm">
          <i class="pi pi-chart-line text-white text-sm font-bold"></i>
        </div>
        <span class="text-xl font-extrabold tracking-tight text-mifi-navy">
          M<span class="text-mifi-cyan">i</span>F<span class="text-mifi-green">i</span>
        </span>
      </router-link>

      <!-- Center Navigation -->
      <div class="flex items-center gap-1 bg-white/40 rounded-full px-2 py-1 border border-white/50">
        <router-link
          v-for="item in navItems"
          :key="item.route"
          :to="item.route"
          class="nav-pill flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium no-underline transition-all duration-200"
          :class="isActive(item.route) ? 'bg-mifi-cyan/15 text-mifi-cyan shadow-sm' : 'text-mifi-navy/60 hover:text-mifi-navy hover:bg-white/60'"
        >
          <i :class="item.icon" class="text-xs"></i>
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <!-- User Section -->
      <div class="flex items-center gap-3">
        <span class="text-sm font-medium text-mifi-navy/70">{{ authStore.user?.nombre || 'Usuario' }}</span>
        <button
          @click="handleLogout"
          class="w-8 h-8 rounded-full bg-mifi-red/10 flex items-center justify-center text-mifi-red hover:bg-mifi-red/20 transition-all duration-200 border-none cursor-pointer"
          title="Cerrar sesión"
        >
          <i class="pi pi-sign-out text-xs"></i>
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto p-6 pt-4">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../../store/auth';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const navItems = [
    { label: 'Dashboard', icon: 'pi pi-home', route: '/' },
    { label: 'Transacciones', icon: 'pi pi-arrow-right-arrow-left', route: '/transactions' },
    { label: 'Cuentas', icon: 'pi pi-wallet', route: '/accounts' },
    { label: 'Recurrentes', icon: 'pi pi-sync', route: '/recurrents' },
    { label: 'Metas', icon: 'pi pi-flag', route: '/goals' },
    { label: 'Categorías', icon: 'pi pi-tags', route: '/categories' },
];

const isActive = (path: string) => {
    if (path === '/') return route.path === '/';
    return route.path.startsWith(path);
};

const handleLogout = () => {
    authStore.logout();
    router.push('/login');
};
</script>
