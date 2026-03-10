<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-mifi-navy m-0">Categorías</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Organiza tus ingresos y gastos por categoría</p>
      </div>
      <Button label="Nueva Categoría" icon="pi pi-plus" @click="showCreate = true" class="!bg-mifi-cyan !border-none !text-white" />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Ingresos -->
      <div class="glass-card p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 rounded-full bg-mifi-green/15 flex items-center justify-center"><i class="pi pi-arrow-up text-mifi-green text-sm"></i></div>
          <h3 class="text-base font-bold text-mifi-navy m-0">Ingresos</h3>
        </div>
        <div v-for="cat in incomeCategories" :key="cat.id" class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
          <span class="text-sm text-mifi-navy">{{ cat.nombre }}</span>
          <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(cat)" />
        </div>
        <div v-if="incomeCategories.length === 0" class="text-center py-4 text-mifi-navy/30 text-sm">Sin categorías de ingreso</div>
      </div>

      <!-- Gastos Fijos -->
      <div class="glass-card p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 rounded-full bg-mifi-red/15 flex items-center justify-center"><i class="pi pi-lock text-mifi-red text-sm"></i></div>
          <h3 class="text-base font-bold text-mifi-navy m-0">Gastos Fijos</h3>
        </div>
        <div v-for="cat in fixedExpenseCategories" :key="cat.id" class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
          <span class="text-sm text-mifi-navy">{{ cat.nombre }}</span>
          <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(cat)" />
        </div>
        <div v-if="fixedExpenseCategories.length === 0" class="text-center py-4 text-mifi-navy/30 text-sm">Sin categorías de gasto fijo</div>
      </div>

      <!-- Gastos Variables -->
      <div class="glass-card p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 rounded-full bg-orange-500/15 flex items-center justify-center"><i class="pi pi-shopping-cart text-orange-500 text-sm"></i></div>
          <h3 class="text-base font-bold text-mifi-navy m-0">Gastos Variables</h3>
        </div>
        <div v-for="cat in variableExpenseCategories" :key="cat.id" class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
          <span class="text-sm text-mifi-navy">{{ cat.nombre }}</span>
          <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(cat)" />
        </div>
        <div v-if="variableExpenseCategories.length === 0" class="text-center py-4 text-mifi-navy/30 text-sm">Sin categorías de gasto variable</div>
      </div>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreate" header="Nueva Categoría" :modal="true" :style="{ width: '400px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Nombre</label>
          <InputText v-model="form.nombre" placeholder="Ej: Alimentación" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Tipo</label>
          <Select v-model="form.tipo" :options="tipoOptions" optionLabel="label" optionValue="value" placeholder="Selecciona tipo" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showCreate = false" />
        <Button label="Crear" icon="pi pi-check" @click="createCategory" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>

    <!-- Confirm Delete Dialog -->
    <Dialog v-model:visible="showConfirm" header="Confirmar eliminación" :modal="true" :style="{ width: '380px' }">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-triangle text-amber-500 text-2xl"></i>
        <p class="text-sm text-mifi-navy m-0">¿Eliminar la categoría <strong>{{ catToDelete?.nombre }}</strong>?</p>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showConfirm = false" />
        <Button label="Sí, eliminar" severity="danger" @click="deleteConfirmed" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { apiClient } from '../api/client';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';
import Select from 'primevue/select';

const categories = ref<any[]>([]);
const showCreate = ref(false);
const showConfirm = ref(false);
const catToDelete = ref<any>(null);
const form = ref({ nombre: '', tipo: 'GASTO_VARIABLE' });

const tipoOptions = [
    { label: 'Ingreso', value: 'INGRESO' },
    { label: 'Gasto Fijo', value: 'GASTO_FIJO' },
    { label: 'Gasto Variable', value: 'GASTO_VARIABLE' },
    { label: 'Cuota Préstamo', value: 'PRESTAMO_CUOTA' },
    { label: 'Ahorro', value: 'AHORRO' },
];

const incomeCategories = computed(() => categories.value.filter(c => c.tipo === 'INGRESO'));
const fixedExpenseCategories = computed(() => categories.value.filter(c => c.tipo === 'GASTO_FIJO'));
const variableExpenseCategories = computed(() => categories.value.filter(c => c.tipo === 'GASTO_VARIABLE' || c.tipo === 'PRESTAMO_CUOTA' || c.tipo === 'AHORRO'));

const fetchCategories = async () => {
  try { categories.value = (await apiClient.get('/categorias/')).data; } catch { /* empty */ }
};

const createCategory = async () => {
  try {
    await apiClient.post('/categorias/', form.value);
    showCreate.value = false;
    form.value = { nombre: '', tipo: 'GASTO_VARIABLE' };
    await fetchCategories();
  } catch { /* empty */ }
};

const confirmDelete = (cat: any) => {
  catToDelete.value = cat;
  showConfirm.value = true;
};

const deleteConfirmed = async () => {
  if (!catToDelete.value) return;
  try {
    await apiClient.delete(`/categorias/${catToDelete.value.id}`);
    showConfirm.value = false;
    catToDelete.value = null;
    await fetchCategories();
  } catch { /* empty */ }
};

onMounted(fetchCategories);
</script>
