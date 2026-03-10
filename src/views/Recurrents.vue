<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-mifi-navy m-0">Movimientos Recurrentes</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Salarios, gastos fijos y pagos que se repiten cada mes</p>
      </div>
      <div class="flex gap-2">
        <Button label="Aplicar al mes" icon="pi pi-sync" @click="applyMonth" class="!bg-mifi-green !border-none !text-white" :loading="applying" />
        <Button label="Nuevo Recurrente" icon="pi pi-plus" @click="openCreate" class="!bg-mifi-cyan !border-none !text-white" />
      </div>
    </div>

    <!-- Ingresos recurrentes -->
    <div class="glass-card p-5">
      <div class="flex items-center gap-2 mb-4">
        <div class="w-8 h-8 rounded-full bg-mifi-green/15 flex items-center justify-center"><i class="pi pi-arrow-up text-mifi-green text-sm"></i></div>
        <h3 class="text-base font-bold text-mifi-navy m-0">Ingresos Mensuales</h3>
      </div>
      <div v-for="r in incomeRecurrents" :key="r.id" class="flex items-center justify-between py-3 border-b border-mifi-navy/5 last:border-0">
        <div>
          <p class="text-sm font-medium text-mifi-navy m-0">{{ r.nombre }}</p>
          <p class="text-xs text-mifi-navy/40 m-0">Día {{ r.dia_mes }} · {{ cuentaNombre(r.cuenta_id) }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-base font-bold text-mifi-green">${{ Number(r.monto).toLocaleString('es-CO') }}</span>
          <Button icon="pi pi-pencil" text rounded severity="info" size="small" @click="openEdit(r)" />
          <Button icon="pi pi-times" text rounded severity="secondary" size="small" @click="confirmDeactivate(r)" />
        </div>
      </div>
      <div v-if="incomeRecurrents.length === 0" class="text-center py-3 text-mifi-navy/30 text-sm">Sin ingresos recurrentes</div>
    </div>

    <!-- Gastos recurrentes -->
    <div class="glass-card p-5">
      <div class="flex items-center gap-2 mb-4">
        <div class="w-8 h-8 rounded-full bg-mifi-red/15 flex items-center justify-center"><i class="pi pi-arrow-down text-mifi-red text-sm"></i></div>
        <h3 class="text-base font-bold text-mifi-navy m-0">Gastos Mensuales Fijos</h3>
      </div>
      <div v-for="r in expenseRecurrents" :key="r.id" class="flex items-center justify-between py-3 border-b border-mifi-navy/5 last:border-0">
        <div>
          <p class="text-sm font-medium text-mifi-navy m-0">{{ r.nombre }}</p>
          <p class="text-xs text-mifi-navy/40 m-0">Día {{ r.dia_mes }} · {{ cuentaNombre(r.cuenta_id) }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-base font-bold text-mifi-red">${{ Number(r.monto).toLocaleString('es-CO') }}</span>
          <Button icon="pi pi-pencil" text rounded severity="info" size="small" @click="openEdit(r)" />
          <Button icon="pi pi-times" text rounded severity="secondary" size="small" @click="confirmDeactivate(r)" />
        </div>
      </div>
      <div v-if="expenseRecurrents.length === 0" class="text-center py-3 text-mifi-navy/30 text-sm">Sin gastos recurrentes</div>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog v-model:visible="showForm" :header="editTarget ? 'Editar Recurrente' : 'Nuevo Recurrente'" :modal="true" :style="{ width: '420px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Nombre</label>
          <InputText v-model="form.nombre" placeholder="Ej: Salario Base, Arriendo, Netflix" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Tipo</label>
          <Select v-model="form.tipo" :options="tipoOptions" optionLabel="label" optionValue="value" placeholder="Selecciona tipo" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Cuenta asociada</label>
          <Select v-model="form.cuenta_id" :options="cuentas" optionLabel="nombre" optionValue="id" placeholder="Selecciona cuenta" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Monto mensual</label>
          <InputNumber v-model="form.monto" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Día del mes</label>
          <InputNumber v-model="form.dia_mes" :min="1" :max="31" suffix=" del mes" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showForm = false" />
        <Button :label="editTarget ? 'Guardar' : 'Crear'" icon="pi pi-check" @click="saveRecurrent" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>

    <!-- Confirm -->
    <Dialog v-model:visible="showConfirm" header="Confirmar desactivación" :modal="true" :style="{ width: '380px' }">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-triangle text-amber-500 text-2xl"></i>
        <p class="text-sm text-mifi-navy m-0">¿Desactivar <strong>{{ toDeactivate?.nombre }}</strong>? No se borrará el histórico.</p>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showConfirm = false" />
        <Button label="Sí, desactivar" severity="danger" @click="deactivateRecurrent" />
      </template>
    </Dialog>

    <!-- Apply result -->
    <Dialog v-model:visible="showResult" header="Resultado" :modal="true" :style="{ width: '350px' }">
      <p class="text-sm text-mifi-navy m-0">{{ applyMessage }}</p>
      <template #footer>
        <Button label="Ok" @click="showResult = false" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { apiClient } from '../api/client';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dialog from 'primevue/dialog';
import Select from 'primevue/select';

const recurrents = ref<any[]>([]);
const cuentas = ref<any[]>([]);
const showForm = ref(false);
const showConfirm = ref(false);
const showResult = ref(false);
const applyMessage = ref('');
const applying = ref(false);
const toDeactivate = ref<any>(null);
const editTarget = ref<any>(null);
const form = ref({ nombre: '', tipo: 'GASTO_FIJO', cuenta_id: null as string | null, monto: 0, dia_mes: 1 });

const tipoOptions = [
    { label: 'Ingreso (Salario, Freelance)', value: 'INGRESO' },
    { label: 'Gasto Fijo (Arriendo, Servicios)', value: 'GASTO_FIJO' },
    { label: 'Cuota Préstamo', value: 'PRESTAMO_CUOTA' },
    { label: 'Ahorro Automático', value: 'AHORRO' },
];

const incomeRecurrents = computed(() => recurrents.value.filter(r => r.tipo === 'INGRESO'));
const expenseRecurrents = computed(() => recurrents.value.filter(r => r.tipo !== 'INGRESO'));
const cuentaNombre = (cid: string) => cuentas.value.find(c => c.id === cid)?.nombre || '';

const fetchData = async () => {
  try {
    const [rRes, cRes] = await Promise.all([apiClient.get('/recurrentes/'), apiClient.get('/cuentas/')]);
    recurrents.value = rRes.data;
    cuentas.value = cRes.data;
  } catch { /* empty */ }
};

const openCreate = () => {
  editTarget.value = null;
  form.value = { nombre: '', tipo: 'GASTO_FIJO', cuenta_id: null, monto: 0, dia_mes: 1 };
  showForm.value = true;
};

const openEdit = (r: any) => {
  editTarget.value = r;
  form.value = { nombre: r.nombre, tipo: r.tipo, cuenta_id: r.cuenta_id, monto: Number(r.monto), dia_mes: r.dia_mes };
  showForm.value = true;
};

const saveRecurrent = async () => {
  try {
    if (editTarget.value) {
      await apiClient.put(`/recurrentes/${editTarget.value.id}`, form.value);
    } else {
      await apiClient.post('/recurrentes/', form.value);
    }
    showForm.value = false;
    editTarget.value = null;
    form.value = { nombre: '', tipo: 'GASTO_FIJO', cuenta_id: null, monto: 0, dia_mes: 1 };
    await fetchData();
  } catch { /* empty */ }
};

const confirmDeactivate = (r: any) => { toDeactivate.value = r; showConfirm.value = true; };

const deactivateRecurrent = async () => {
  if (!toDeactivate.value) return;
  try {
    await apiClient.delete(`/recurrentes/${toDeactivate.value.id}`);
    showConfirm.value = false;
    toDeactivate.value = null;
    await fetchData();
  } catch { /* empty */ }
};

const applyMonth = async () => {
  applying.value = true;
  try {
    const res = await apiClient.post('/recurrentes/aplicar-mes');
    applyMessage.value = res.data.message;
    showResult.value = true;
    await fetchData();
  } catch { applyMessage.value = 'Error aplicando recurrentes'; showResult.value = true; }
  finally { applying.value = false; }
};

onMounted(fetchData);
</script>
