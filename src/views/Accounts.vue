<template>
  <div class="space-y-6 soft-enter">
    <div class="flex items-end justify-between">
      <div>
        <span class="eyebrow">Tu dinero</span>
        <h1 class="text-3xl font-bold font-display tracking-tight text-mifi-navy m-0 mt-2">Cuentas</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Administra tus cuentas bancarias, tarjetas y efectivo</p>
      </div>
      <Button label="Nueva Cuenta" icon="pi pi-plus" @click="showCreate = true" class="!bg-mifi-cyan !border-none !text-white" />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="account in accounts" :key="account.id" class="glass-card p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="iconBg(account.tipo)">
              <i :class="iconClass(account.tipo)" class="text-base"></i>
            </div>
            <div>
              <p class="text-sm font-bold text-mifi-navy m-0">{{ account.nombre }}</p>
              <p class="text-xs text-mifi-navy/50 m-0">
                {{ tipoLabel(account.tipo) }}
                <span v-if="account.es_nomina" class="text-mifi-cyan font-bold ml-1">· NÓMINA</span>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <Button v-if="account.tipo === 'TARJETA_CREDITO'" icon="pi pi-crosshairs" text rounded
                    :class="account.es_objetivo ? '!text-mifi-red' : '!text-mifi-navy/30'"
                    :title="account.es_objetivo ? 'Deuda objetivo actual' : 'Marcar como deuda objetivo'"
                    @click="setObjetivo(account)" />
            <Button icon="pi pi-pencil" text rounded severity="secondary" @click="openEdit(account)" title="Editar" />
            <Button icon="pi pi-times" text rounded severity="secondary" @click="confirmDeactivate(account)" title="Desactivar" />
          </div>
        </div>
        <div v-if="account.es_objetivo" class="inline-flex items-center gap-1 text-xs font-bold text-mifi-red bg-mifi-red/10 px-2 py-0.5 rounded-full mb-2">
          <i class="pi pi-crosshairs text-[10px]"></i> Objetivo (bola de nieve)
        </div>

        <p class="text-2xl font-bold font-display tnum m-0"
           :class="account.tipo === 'TARJETA_CREDITO' ? 'text-mifi-red' : (Number(account.saldo) >= 0 ? 'text-mifi-green' : 'text-mifi-red')">
          ${{ Number(account.saldo).toLocaleString('es-CO') }}
        </p>
        <p class="text-xs text-mifi-navy/40 m-0 mt-1">
            {{ account.tipo === 'TARJETA_CREDITO' ? 'Deuda actual (consumido)' : 'Saldo disponible' }}
        </p>

        <!-- Credit card progress bar -->
        <div v-if="account.tipo === 'TARJETA_CREDITO' && account.cupo_total" class="mt-3">
          <div class="flex justify-between text-xs text-mifi-navy/40 mb-1 tnum">
            <span>Disponible: ${{ Math.max(Number(account.cupo_total) - Number(account.saldo), 0).toLocaleString('es-CO') }}</span>
            <span>Cupo: ${{ Number(account.cupo_total).toLocaleString('es-CO') }}</span>
          </div>
          <div class="h-2.5 bg-mifi-navy/5 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500 ease-soft"
              :class="cardUsagePct(account) > 80 ? 'bg-mifi-red' : cardUsagePct(account) > 50 ? 'bg-amber-500' : 'bg-purple-500'"
              :style="{ width: cardUsagePct(account) + '%' }"
            ></div>
          </div>
          <p class="text-right text-xs mt-0.5 m-0" :class="cardUsagePct(account) > 80 ? 'text-mifi-red' : 'text-mifi-navy/40'">{{ cardUsagePct(account) }}% usado</p>
        </div>
      </div>

      <div v-if="accounts.length === 0" class="glass-card p-8 flex flex-col items-center justify-center text-mifi-navy/30 col-span-full">
        <i class="pi pi-wallet text-4xl mb-3"></i>
        <p class="text-sm">No tienes cuentas registradas</p>
      </div>
    </div>

    <!-- Create Dialog -->
    <Dialog v-model:visible="showCreate" header="Nueva Cuenta" :modal="true" :style="{ width: '420px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Nombre</label>
          <InputText v-model="form.nombre" placeholder="Ej: Bancolombia Ahorros" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Tipo de cuenta</label>
          <Select v-model="form.tipo" :options="tipoOptions" optionLabel="label" optionValue="value" placeholder="Selecciona tipo" />
        </div>
        <div class="flex flex-col gap-2" v-if="form.tipo === 'TARJETA_CREDITO'">
          <label class="font-medium text-sm text-mifi-navy">Cupo total de la tarjeta</label>
          <InputNumber v-model="form.cupo_total" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">{{ form.tipo === 'TARJETA_CREDITO' ? 'Deuda actual (lo que ya has consumido)' : 'Saldo inicial' }}</label>
          <InputNumber v-model="form.saldo_inicial" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2" v-if="form.tipo === 'TARJETA_CREDITO'">
          <label class="font-medium text-sm text-mifi-navy">Cuota mensual (pago mínimo)</label>
          <InputNumber v-model="form.cuota_mensual" mode="currency" currency="COP" locale="es-CO" />
          <small class="text-mifi-navy/40">Se usa para proyectar la bola de nieve si la marcas como objetivo.</small>
        </div>
        <div class="flex items-center gap-3" v-if="form.tipo !== 'TARJETA_CREDITO'">
          <input type="checkbox" id="esNomina" v-model="form.es_nomina" class="w-4 h-4 accent-mifi-cyan" />
          <label for="esNomina" class="text-sm text-mifi-navy">¿Es tu cuenta de nómina?</label>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showCreate = false" />
        <Button label="Crear" icon="pi pi-check" @click="createAccount" class="!bg-mifi-cyan !border-none !text-white" />
      </template>
    </Dialog>

    <!-- Confirm Deactivate Dialog -->
    <Dialog v-model:visible="showConfirm" header="Confirmar desactivación" :modal="true" :style="{ width: '380px' }">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-triangle text-amber-500 text-2xl"></i>
        <p class="text-sm text-mifi-navy m-0">
          ¿Estás seguro de desactivar la cuenta <strong>{{ accountToDelete?.nombre }}</strong>? No se borrará, solo dejará de aparecer.
        </p>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showConfirm = false" />
        <Button label="Sí, desactivar" severity="danger" @click="deactivateAccount" />
      </template>
    </Dialog>

    <!-- Edit Dialog -->
    <Dialog v-model:visible="showEdit" header="Editar Cuenta" :modal="true" :style="{ width: '420px' }">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Nombre</label>
          <InputText v-model="editForm.nombre" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">Tipo de cuenta</label>
          <Select v-model="editForm.tipo" :options="tipoOptions" optionLabel="label" optionValue="value" />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm text-mifi-navy">{{ editForm.tipo === 'TARJETA_CREDITO' ? 'Deuda actual (consumido)' : 'Saldo' }}</label>
          <InputNumber v-model="editForm.saldo" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex flex-col gap-2" v-if="editForm.tipo === 'TARJETA_CREDITO'">
          <label class="font-medium text-sm text-mifi-navy">Cupo total</label>
          <InputNumber v-model="editForm.cupo_total" mode="currency" currency="COP" locale="es-CO" />
        </div>
        <div class="flex items-center gap-3" v-if="editForm.tipo !== 'TARJETA_CREDITO'">
          <input type="checkbox" id="editNomina" v-model="editForm.es_nomina" class="w-4 h-4 accent-mifi-cyan" />
          <label for="editNomina" class="text-sm text-mifi-navy">¿Es tu cuenta de nómina?</label>
        </div>
      </div>
      <template #footer>
        <Button label="Cancelar" text @click="showEdit = false" />
        <Button label="Guardar" icon="pi pi-check" @click="saveEdit" class="!bg-mifi-cyan !border-none !text-white" />
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

const accounts = ref<any[]>([]);
const showCreate = ref(false);
const showConfirm = ref(false);
const showEdit = ref(false);
const accountToDelete = ref<any>(null);
const editingAccount = ref<any>(null);
const form = ref({ nombre: '', tipo: 'CUENTA_AHORROS', saldo_inicial: 0, cupo_total: null as number | null, cuota_mensual: null as number | null, es_nomina: false });
const editForm = ref({ nombre: '', tipo: 'CUENTA_AHORROS', saldo: 0, cupo_total: null as number | null, cuota_mensual: null as number | null, es_nomina: false });

const tipoOptions = [
    { label: 'Cuenta de Ahorros', value: 'CUENTA_AHORROS' },
    { label: 'Cuenta Corriente', value: 'CUENTA_CORRIENTE' },
    { label: 'Tarjeta de Crédito', value: 'TARJETA_CREDITO' },
    { label: 'Efectivo', value: 'EFECTIVO' },
    { label: 'Billetera Digital (Nequi, Daviplata)', value: 'BILLETERA_DIGITAL' },
    { label: 'Otro', value: 'OTRO' },
];

const tipoLabel = (tipo: string) => tipoOptions.find(t => t.value === tipo)?.label || tipo;

const iconBg = (tipo: string) => {
    const map: Record<string, string> = {
        'TARJETA_CREDITO': 'bg-purple-500/15',
        'CUENTA_AHORROS': 'bg-mifi-cyan/15',
        'CUENTA_CORRIENTE': 'bg-blue-500/15',
        'EFECTIVO': 'bg-mifi-green/15',
        'BILLETERA_DIGITAL': 'bg-amber-500/15',
    };
    return map[tipo] || 'bg-mifi-navy/10';
};

const iconClass = (tipo: string) => {
    const map: Record<string, string> = {
        'TARJETA_CREDITO': 'pi pi-credit-card text-purple-500',
        'CUENTA_AHORROS': 'pi pi-building-columns text-mifi-cyan',
        'CUENTA_CORRIENTE': 'pi pi-building text-blue-500',
        'EFECTIVO': 'pi pi-money-bill text-mifi-green',
        'BILLETERA_DIGITAL': 'pi pi-mobile text-amber-500',
    };
    return map[tipo] || 'pi pi-wallet text-mifi-navy/60';
};

const cardUsagePct = (account: any) => {
    const total = Number(account.cupo_total) || 1;
    const consumido = Number(account.saldo) || 0;  // saldo (TC) = deuda consumida
    return Math.min(100, Math.round((consumido / total) * 100));
};

const fetchAccounts = async () => {
  try {
    const res = await apiClient.get('/cuentas/');
    accounts.value = res.data;
  } catch { /* empty */ }
};

const createAccount = async () => {
  try {
    const payload: any = { ...form.value };
    // TC: cupo_total = límite; saldo_inicial = deuda ya consumida (puede ser 0)
    if (form.value.tipo !== 'TARJETA_CREDITO') {
      payload.cupo_total = null;
    }
    await apiClient.post('/cuentas/', payload);
    showCreate.value = false;
    form.value = { nombre: '', tipo: 'CUENTA_AHORROS', saldo_inicial: 0, cupo_total: null, cuota_mensual: null, es_nomina: false };
    await fetchAccounts();
  } catch { /* empty */ }
};

const setObjetivo = async (account: any) => {
  try {
    await apiClient.put(`/cuentas/${account.id}`, { es_objetivo: !account.es_objetivo });
    await fetchAccounts();
  } catch { /* empty */ }
};

const confirmDeactivate = (account: any) => {
    accountToDelete.value = account;
    showConfirm.value = true;
};

const deactivateAccount = async () => {
  if (!accountToDelete.value) return;
  try {
    await apiClient.delete(`/cuentas/${accountToDelete.value.id}`);
    showConfirm.value = false;
    accountToDelete.value = null;
    await fetchAccounts();
  } catch { /* empty */ }
};

const openEdit = (account: any) => {
  editingAccount.value = account;
  editForm.value = {
    nombre: account.nombre,
    tipo: account.tipo,
    saldo: Number(account.saldo),
    cupo_total: account.cupo_total ? Number(account.cupo_total) : null,
    cuota_mensual: account.cuota_mensual ? Number(account.cuota_mensual) : null,
    es_nomina: account.es_nomina,
  };
  showEdit.value = true;
};

const saveEdit = async () => {
  if (!editingAccount.value) return;
  try {
    const payload: any = { ...editForm.value };
    // TC: saldo = deuda consumida, cupo_total = límite (ambos van tal cual)
    if (editForm.value.tipo !== 'TARJETA_CREDITO') {
      payload.cupo_total = null;
    }
    await apiClient.put(`/cuentas/${editingAccount.value.id}`, payload);
    showEdit.value = false;
    editingAccount.value = null;
    await fetchAccounts();
  } catch { /* empty */ }
};

onMounted(fetchAccounts);
</script>
