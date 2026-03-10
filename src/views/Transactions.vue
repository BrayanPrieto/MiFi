<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-mifi-navy m-0">Transacciones</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Historial de ingresos y gastos</p>
      </div>
      <Button label="Nueva Transacción" icon="pi pi-plus" @click="showCreate = true" class="!bg-mifi-cyan !border-none !text-white" />
    </div>

    <!-- Filters -->
    <div class="glass-card p-4 flex items-center gap-4 flex-wrap">
      <Select v-model="selectedCuenta" :options="cuentas" optionLabel="nombre" placeholder="Todas las Cuentas" class="w-56" showClear />
      <Select v-model="selectedTipo" :options="tipoOptions" optionLabel="label" optionValue="value" placeholder="Todos los tipos" class="w-48" showClear />
    </div>

    <!-- Summary  -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4" v-if="transacciones.length > 0">
      <div class="glass-card p-4 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-mifi-green/15 flex items-center justify-center">
          <i class="pi pi-arrow-up text-mifi-green text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-mifi-navy/50 m-0">Ingresos del mes</p>
          <p class="text-lg font-bold text-mifi-green m-0">${{ totalIncome.toLocaleString('es-CO') }}</p>
        </div>
      </div>
      <div class="glass-card p-4 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-mifi-red/15 flex items-center justify-center">
          <i class="pi pi-arrow-down text-mifi-red text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-mifi-navy/50 m-0">Gastos del mes</p>
          <p class="text-lg font-bold text-mifi-red m-0">${{ totalExpenses.toLocaleString('es-CO') }}</p>
        </div>
      </div>
      <div class="glass-card p-4 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-mifi-cyan/15 flex items-center justify-center">
          <i class="pi pi-chart-line text-mifi-cyan text-sm"></i>
        </div>
        <div>
          <p class="text-xs text-mifi-navy/50 m-0">Balance del mes</p>
          <p class="text-lg font-bold m-0" :class="totalBalance >= 0 ? 'text-mifi-green' : 'text-mifi-red'">${{ totalBalance.toLocaleString('es-CO') }}</p>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <DataTable 
        :value="filteredTransactions" 
        paginator :rows="10" 
        :loading="loading"
        dataKey="id"
        tableStyle="min-width: 50rem"
        class="p-datatable-sm"
      >
        <template #empty>
          <div class="flex flex-col items-center justify-center py-12 text-mifi-navy/30">
            <i class="pi pi-inbox text-3xl mb-2"></i>
            <p class="text-sm">No hay transacciones registradas</p>
          </div>
        </template>
        
        <Column field="fecha" header="Fecha" sortable style="width: 12%">
           <template #body="{ data }">
                <span class="text-sm font-medium text-mifi-navy/70">{{ formatDate(data.fecha) }}</span>
           </template>
        </Column>

        <Column header="Tipo" style="width: 15%">
            <template #body="{ data }">
                <span class="text-xs px-2 py-1 rounded-full font-medium" :class="tipoBadge(data.tipo)">
                    {{ tipoLabel(data.tipo) }}
                </span>
            </template>
        </Column>
        
        <Column header="Descripción" style="width: 35%">
             <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-medium text-mifi-navy">{{ data.descripcion || 'Sin descripción' }}</span>
                  <i v-if="data.fuente_ia" class="pi pi-sparkles text-mifi-cyan text-xs" title="Registrado por IA"></i>
                </div>
             </template>
        </Column>
        
        <Column header="Monto" style="width: 15%">
            <template #body="{ data }">
                <span 
                    class="text-sm font-bold whitespace-nowrap" 
                    :class="data.tipo === 'INGRESO' ? 'text-mifi-green' : 'text-mifi-red'"
                >
                   {{ data.tipo === 'INGRESO' ? '+' : '-' }} ${{ Number(data.monto).toLocaleString('es-CO') }}
                </span>
            </template>
        </Column>

        <Column header="" style="width: 5%">
            <template #body="{ data }">
              <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(data)" />
            </template>
        </Column>
      </DataTable>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreate" header="Nueva Transacción" :modal="true" :style="{ width: '450px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Tipo</label>
          <Select v-model="form.tipo" :options="allTipoOptions" optionLabel="label" optionValue="value" placeholder="Selecciona tipo" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Cuenta</label>
          <Select v-model="form.cuenta_id" :options="cuentas" optionLabel="nombre" optionValue="id" placeholder="Selecciona cuenta" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Monto</label>
          <InputNumber v-model="form.monto" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Descripción</label>
          <InputText v-model="form.descripcion" placeholder="Ej: Pago de servicios" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Fecha</label>
          <InputText v-model="form.fecha" type="date" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showCreate = false" />
        <Button label="Registrar" icon="pi pi-check" @click="createTransaction" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>

    <!-- Confirm Delete -->
    <Dialog v-model:visible="showConfirm" header="Confirmar eliminación" :modal="true" :style="{ width: '380px' }">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-triangle text-amber-500 text-2xl"></i>
        <p class="text-sm text-mifi-navy m-0">¿Eliminar esta transacción de <strong>${{ Number(txToDelete?.monto || 0).toLocaleString('es-CO') }}</strong>?</p>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showConfirm = false" />
        <Button label="Sí, eliminar" severity="danger" @click="deleteTransaction" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { apiClient } from '../api/client';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Select from 'primevue/select';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dialog from 'primevue/dialog';

const transacciones = ref<any[]>([]);
const cuentas = ref<any[]>([]);
const loading = ref(true);
const showCreate = ref(false);
const showConfirm = ref(false);
const txToDelete = ref<any>(null);
const selectedCuenta = ref(null);
const selectedTipo = ref(null);

const today = new Date().toISOString().slice(0, 10);
const form = ref({ tipo: 'GASTO_VARIABLE', cuenta_id: null as string | null, monto: 0, descripcion: '', fecha: today });

const tipoOptions = [
    { label: 'Ingresos', value: 'INGRESO' },
    { label: 'Gastos Fijos', value: 'GASTO_FIJO' },
    { label: 'Gastos Variables', value: 'GASTO_VARIABLE' },
];

const allTipoOptions = [
    { label: 'Ingreso', value: 'INGRESO' },
    { label: 'Gasto Fijo', value: 'GASTO_FIJO' },
    { label: 'Gasto Variable', value: 'GASTO_VARIABLE' },
    { label: 'Cuota Préstamo', value: 'PRESTAMO_CUOTA' },
    { label: 'Ahorro', value: 'AHORRO' },
];

const tipoLabel = (tipo: string) => allTipoOptions.find(t => t.value === tipo)?.label || tipo;

const tipoBadge = (tipo: string) => {
    const map: Record<string, string> = {
        'INGRESO': 'bg-mifi-green/15 text-mifi-green',
        'GASTO_FIJO': 'bg-mifi-red/15 text-mifi-red',
        'GASTO_VARIABLE': 'bg-orange-500/15 text-orange-600',
        'PRESTAMO_CUOTA': 'bg-purple-500/15 text-purple-600',
        'AHORRO': 'bg-mifi-cyan/15 text-mifi-cyan',
    };
    return map[tipo] || 'bg-mifi-navy/10 text-mifi-navy';
};

const totalIncome = computed(() => transacciones.value.filter(t => t.tipo === 'INGRESO').reduce((s, t) => s + Number(t.monto), 0));
const totalExpenses = computed(() => transacciones.value.filter(t => t.tipo !== 'INGRESO').reduce((s, t) => s + Number(t.monto), 0));
const totalBalance = computed(() => totalIncome.value - totalExpenses.value);

const filteredTransactions = computed(() => {
    let result = transacciones.value;
    if (selectedTipo.value) result = result.filter((t: any) => t.tipo === selectedTipo.value);
    if (selectedCuenta.value) result = result.filter((t: any) => t.cuenta_id === (selectedCuenta.value as any).id);
    return result;
});

const formatDate = (dateString: string) => {
    return new Date(dateString + 'T00:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
};

const fetchData = async () => {
    loading.value = true;
    try {
        const [txRes, accRes] = await Promise.all([
            apiClient.get('/transacciones/'),
            apiClient.get('/cuentas/')
        ]);
        transacciones.value = txRes.data;
        cuentas.value = accRes.data;
    } catch { /* empty */ } finally {
        loading.value = false;
    }
};

const createTransaction = async () => {
    if (!form.value.cuenta_id) {
        alert('Selecciona una cuenta');
        return;
    }
    try {
        await apiClient.post('/transacciones/', form.value);
        showCreate.value = false;
        form.value = { tipo: 'GASTO_VARIABLE', cuenta_id: null, monto: 0, descripcion: '', fecha: today };
        await fetchData();
    } catch (e: any) {
        console.error('Error creando transacción', e?.response?.data);
    }
};

const confirmDelete = (tx: any) => {
    txToDelete.value = tx;
    showConfirm.value = true;
};

const deleteTransaction = async () => {
    if (!txToDelete.value) return;
    try {
        await apiClient.delete(`/transacciones/${txToDelete.value.id}`);
        showConfirm.value = false;
        txToDelete.value = null;
        await fetchData();
    } catch { /* empty */ }
};

onMounted(fetchData);
</script>
