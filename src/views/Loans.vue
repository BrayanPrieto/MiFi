<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-mifi-navy m-0">Préstamos</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Control de tus deudas y préstamos activos</p>
      </div>
      <Button label="Nuevo Préstamo" icon="pi pi-plus" @click="showCreate = true" class="!bg-mifi-cyan !border-none !text-white" />
    </div>

    <!-- Totales -->
    <div class="glass-card p-4 flex items-center justify-between" v-if="loans.length > 0">
      <div>
        <p class="text-xs text-mifi-navy/50 m-0">Deuda total</p>
        <p class="text-lg font-bold text-mifi-red m-0">${{ Number(totalDeuda).toLocaleString('es-CO') }}</p>
      </div>
      <div class="text-right">
        <p class="text-xs text-mifi-navy/50 m-0">Cuotas mensuales</p>
        <p class="text-lg font-bold text-orange-500 m-0">${{ Number(totalCuotas).toLocaleString('es-CO') }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="loan in loans" :key="loan.id" class="glass-card p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 rounded-xl bg-mifi-red/15 flex items-center justify-center">
              <i class="pi pi-money-bill text-mifi-red"></i>
            </div>
            <div>
              <p class="text-sm font-bold text-mifi-navy m-0">{{ loan.entidad }}</p>
              <p class="text-xs text-mifi-navy/50 m-0 capitalize">{{ loan.tipo }} · {{ loan.estado }}</p>
            </div>
          </div>
          <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDelete(loan)" />
        </div>
        <div class="flex justify-between items-end">
          <div>
            <p class="text-xs text-mifi-navy/50 m-0">Saldo pendiente</p>
            <p class="text-xl font-bold text-mifi-red m-0">${{ Number(loan.saldo_pendiente || 0).toLocaleString('es-CO') }}</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-mifi-navy/50 m-0">Monto total</p>
            <p class="text-sm font-medium text-mifi-navy m-0">${{ Number(loan.monto_total || 0).toLocaleString('es-CO') }}</p>
          </div>
        </div>
        <div class="mt-3 h-2 bg-mifi-navy/5 rounded-full overflow-hidden">
          <div class="h-full bg-gradient-to-r from-mifi-cyan to-mifi-green rounded-full transition-all" :style="{ width: progressPercent(loan) + '%' }"></div>
        </div>
        <p class="text-xs text-mifi-navy/40 mt-1 m-0 text-right">{{ progressPercent(loan) }}% pagado</p>
      </div>

      <div v-if="loans.length === 0" class="glass-card p-8 flex flex-col items-center justify-center text-mifi-navy/30 col-span-full">
        <i class="pi pi-money-bill text-4xl mb-3"></i>
        <p class="text-sm">No tienes préstamos registrados</p>
      </div>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreate" header="Nuevo Préstamo" :modal="true" :style="{ width: '450px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Entidad o persona</label>
          <InputText v-model="form.entidad" placeholder="Ej: Bancolombia, Elba" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Tipo</label>
          <Select v-model="form.tipo" :options="tipoOptions" optionLabel="label" optionValue="value" placeholder="Tipo de préstamo" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Monto total del préstamo</label>
          <InputNumber v-model="form.monto_total" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Saldo pendiente actual</label>
          <InputNumber v-model="form.saldo_pendiente" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Cuota mensual</label>
          <InputNumber v-model="form.cuota_mensual_esperada" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Día de pago</label>
          <InputNumber v-model="form.dia_pago" :min="1" :max="31" suffix=" del mes" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Cuenta desde la que se paga</label>
          <Select v-model="form.cuenta_pago_id" :options="cuentas" optionLabel="nombre" optionValue="id" placeholder="Selecciona cuenta" />
          <small class="text-mifi-navy/40">Se creará un recurrente automático</small>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showCreate = false" />
        <Button label="Crear" icon="pi pi-check" @click="createLoan" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>

    <!-- Confirm Delete -->
    <Dialog v-model:visible="showConfirm" header="Confirmar eliminación" :modal="true" :style="{ width: '380px' }">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-triangle text-amber-500 text-2xl"></i>
        <p class="text-sm text-mifi-navy m-0">¿Eliminar el préstamo de <strong>{{ loanToDelete?.entidad }}</strong>?</p>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showConfirm = false" />
        <Button label="Sí, eliminar" severity="danger" @click="deleteLoan" />
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
import Select from 'primevue/select';

const loans = ref<any[]>([]);
const cuentas = ref<any[]>([]);
const showCreate = ref(false);
const showConfirm = ref(false);
const loanToDelete = ref<any>(null);
const form = ref({ entidad: '', tipo: 'BANCO', monto_total: 0, saldo_pendiente: 0, cuota_mensual_esperada: 0, dia_pago: 1, cuenta_pago_id: null as string | null });

const totalDeuda = ref(0);
const totalCuotas = ref(0);

const tipoOptions = [
    { label: 'Banco', value: 'BANCO' },
    { label: 'Tercero / Personal', value: 'TERCERO' },
];

const progressPercent = (loan: any) => {
  const total = Number(loan.monto_total) || 1;
  const pendiente = Number(loan.saldo_pendiente) || 0;
  return Math.round(((total - pendiente) / total) * 100);
};

const fetchLoans = async () => {
  try {
    const [lRes, cRes] = await Promise.all([
      apiClient.get('/prestamos/'),
      apiClient.get('/cuentas/'),
    ]);
    loans.value = lRes.data;
    cuentas.value = cRes.data;
    totalDeuda.value = loans.value.reduce((s: number, l: any) => s + Number(l.saldo_pendiente || 0), 0);
    totalCuotas.value = loans.value.reduce((s: number, l: any) => s + Number(l.cuota_mensual_esperada || 0), 0);
  } catch { /* empty */ }
};

const createLoan = async () => {
  try {
    await apiClient.post('/prestamos/', form.value);
    showCreate.value = false;
    form.value = { entidad: '', tipo: 'BANCO', monto_total: 0, saldo_pendiente: 0, cuota_mensual_esperada: 0, dia_pago: 1, cuenta_pago_id: null };
    await fetchLoans();
  } catch { /* empty */ }
};

const confirmDelete = (loan: any) => {
    loanToDelete.value = loan;
    showConfirm.value = true;
};

const deleteLoan = async () => {
    if (!loanToDelete.value) return;
    try {
        await apiClient.delete(`/prestamos/${loanToDelete.value.id}`);
        showConfirm.value = false;
        loanToDelete.value = null;
        await fetchLoans();
    } catch { /* empty */ }
};

onMounted(fetchLoans);
</script>
