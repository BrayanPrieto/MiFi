<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-mifi-navy m-0">Metas de Ahorro</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Sigue tu progreso hacia tus objetivos financieros</p>
      </div>
      <Button label="Nueva Meta" icon="pi pi-plus" @click="showCreate = true" class="!bg-mifi-cyan !border-none !text-white" />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="goal in goals" :key="goal.id" class="glass-card p-5">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 rounded-xl bg-mifi-green/15 flex items-center justify-center">
              <i class="pi pi-flag text-mifi-green"></i>
            </div>
            <div>
              <p class="text-sm font-bold text-mifi-navy m-0">{{ goal.nombre }}</p>
              <p class="text-xs text-mifi-navy/50 m-0" v-if="goal.fecha_objetivo">Fecha: {{ new Date(goal.fecha_objetivo).toLocaleDateString('es-CO') }}</p>
            </div>
          </div>
          <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDelete(goal)" />
        </div>

        <div class="flex justify-between text-xs text-mifi-navy/50 mb-1">
          <span>${{ Number(goal.monto_actual || 0).toLocaleString('es-CO') }}</span>
          <span>${{ Number(goal.monto_objetivo || 0).toLocaleString('es-CO') }}</span>
        </div>
        <div class="h-3 bg-mifi-navy/5 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-mifi-cyan to-mifi-green rounded-full transition-all duration-500" :style="{ width: goalProgress(goal) + '%' }"></div>
        </div>
        <p class="text-right text-xs font-bold mt-1 m-0" :class="goalProgress(goal) >= 100 ? 'text-mifi-green' : 'text-mifi-cyan'">
          {{ goalProgress(goal) }}%
        </p>
      </div>

      <div v-if="goals.length === 0" class="glass-card p-8 flex flex-col items-center justify-center text-mifi-navy/30 col-span-full">
        <i class="pi pi-flag text-4xl mb-3"></i>
        <p class="text-sm">No tienes metas registradas</p>
      </div>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreate" header="Nueva Meta de Ahorro" :modal="true" :style="{ width: '420px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Nombre de la meta</label>
          <InputText v-model="form.nombre" placeholder="Ej: Viaje a Europa" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Monto objetivo</label>
          <InputNumber v-model="form.monto_objetivo" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Monto ya ahorrado</label>
          <InputNumber v-model="form.monto_actual" mode="currency" currency="COP" locale="es-CO" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showCreate = false" />
        <Button label="Crear" icon="pi pi-check" @click="createGoal" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>

    <!-- Confirm Delete -->
    <Dialog v-model:visible="showConfirm" header="Confirmar eliminación" :modal="true" :style="{ width: '380px' }">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-triangle text-amber-500 text-2xl"></i>
        <p class="text-sm text-mifi-navy m-0">¿Eliminar la meta <strong>{{ goalToDelete?.nombre }}</strong>?</p>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showConfirm = false" />
        <Button label="Sí, eliminar" severity="danger" @click="deleteGoal" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiClient } from '../api/client';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dialog from 'primevue/dialog';

const goals = ref<any[]>([]);
const showCreate = ref(false);
const showConfirm = ref(false);
const goalToDelete = ref<any>(null);
const form = ref({ nombre: '', monto_objetivo: 0, monto_actual: 0 });

const goalProgress = (goal: any) => {
  const objetivo = Number(goal.monto_objetivo) || 1;
  const actual = Number(goal.monto_actual) || 0;
  return Math.min(100, Math.round((actual / objetivo) * 100));
};

const fetchGoals = async () => {
  try {
    const res = await apiClient.get('/metas/');
    goals.value = res.data;
  } catch { /* empty */ }
};

const createGoal = async () => {
  try {
    await apiClient.post('/metas/', form.value);
    showCreate.value = false;
    form.value = { nombre: '', monto_objetivo: 0, monto_actual: 0 };
    await fetchGoals();
  } catch { /* empty */ }
};

const confirmDelete = (goal: any) => {
    goalToDelete.value = goal;
    showConfirm.value = true;
};

const deleteGoal = async () => {
    if (!goalToDelete.value) return;
    try {
        await apiClient.delete(`/metas/${goalToDelete.value.id}`);
        showConfirm.value = false;
        goalToDelete.value = null;
        await fetchGoals();
    } catch { /* empty */ }
};

onMounted(fetchGoals);
</script>
