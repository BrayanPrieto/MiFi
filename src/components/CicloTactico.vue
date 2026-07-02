<template>
  <div class="space-y-4 soft-enter">
    <!-- Alerta del día de disparo -->
    <div v-if="esDiaDisparo" class="glass-card p-4 flex items-center gap-3 border-2 border-mifi-red/30 bg-mifi-red/5">
      <i class="pi pi-bolt text-mifi-red text-xl animate-pulse"></i>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-bold text-mifi-red">Día de disparo</div>
        <div class="text-xs text-mifi-navy/60">
          Tienes <strong>${{ fmt(resumen.flujo_libre_ajustado) }}</strong> para aniquilar capital
          <template v-if="resumen.deuda_objetivo"> de {{ resumen.deuda_objetivo.entidad }}</template>.
        </div>
      </div>
    </div>

    <!-- Banda táctica: Semáforo · Reloj de liquidez · Deuda objetivo -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <!-- Semáforo de la quincena -->
      <div class="glass-card p-5 flex items-center gap-3.5">
        <span class="w-3.5 h-3.5 rounded-full flex-shrink-0 transition-all duration-700 ease-soft" :class="semaforoDot" :style="{ boxShadow: '0 0 0 4px ' + semaforoGlow }"></span>
        <div class="min-w-0">
          <div class="eyebrow">Quincena {{ resumen.quincena_actual || 1 }}</div>
          <div class="text-base font-bold mt-1" :class="semaforoText">{{ semaforoLabel }}</div>
          <div class="text-xs text-mifi-navy/40 truncate tnum">
            Pendiente ${{ fmt(resumen.pendiente_actual) }} · Disponible ${{ fmt(resumen.saldo_disponible) }}
          </div>
        </div>
      </div>

      <!-- Reloj de liquidez -->
      <div class="glass-card p-5">
        <div class="flex items-center justify-between mb-1.5">
          <span class="eyebrow">Flujo libre</span>
          <i class="pi pi-bolt text-mifi-cyan text-xs"></i>
        </div>
        <div class="text-3xl font-bold font-display tnum" :class="(resumen.flujo_libre_ajustado || 0) >= 0 ? 'text-mifi-green' : 'text-mifi-red'">
          ${{ fmt(resumen.flujo_libre_ajustado) }}
        </div>
        <div class="text-xs text-mifi-navy/40 mt-0.5">Disponible para el día {{ resumen.dia_disparo || 28 }} (disparo)</div>
      </div>

      <!-- Deuda objetivo -->
      <div class="glass-card p-5">
        <div class="flex items-center justify-between mb-1.5">
          <span class="eyebrow">Deuda objetivo</span>
          <i class="pi pi-crosshairs text-mifi-red text-xs"></i>
        </div>
        <template v-if="resumen.deuda_objetivo">
          <div class="flex justify-between items-baseline text-xs mb-1.5">
            <span class="font-bold text-mifi-navy truncate">{{ resumen.deuda_objetivo.entidad }}</span>
            <span class="text-mifi-navy/40 tnum">${{ fmt(resumen.deuda_objetivo.saldo_pendiente) }}</span>
          </div>
          <div class="h-2.5 bg-mifi-navy/5 rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-mifi-cyan to-mifi-green rounded-full transition-all duration-700 ease-soft"
                 :style="{ width: (resumen.deuda_objetivo.progreso_pct || 0) + '%' }"></div>
          </div>
          <div class="flex justify-between text-xs mt-0.5">
            <span class="text-mifi-green">{{ resumen.deuda_objetivo.progreso_pct }}% aniquilado</span>
            <span v-if="resumen.deuda_objetivo.meses_estimados != null" class="text-mifi-navy/40">
              ~{{ resumen.deuda_objetivo.meses_estimados }} {{ resumen.deuda_objetivo.meses_estimados === 1 ? 'mes' : 'meses' }}
            </span>
          </div>
        </template>
        <div v-else class="text-xs text-mifi-navy/40 py-2">
          Sin deuda objetivo. Marca una tarjeta en <router-link to="/accounts" class="text-mifi-cyan no-underline hover:underline">Cuentas</router-link>.
        </div>
      </div>
    </div>

    <!-- Checklist del ciclo -->
    <div class="glass-card p-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-mifi-navy m-0"><i class="pi pi-check-square text-mifi-cyan mr-2"></i>Checklist del ciclo</h3>
        <button v-if="recibos.length === 0" @click="generar" :disabled="loading"
                class="text-xs bg-mifi-cyan text-white px-3 py-1.5 rounded-lg border-none cursor-pointer disabled:opacity-50">
          <i class="pi pi-plus mr-1"></i>Generar mes
        </button>
      </div>

      <div v-if="recibos.length === 0" class="text-center py-4 text-mifi-navy/30 text-xs">
        Aún no has generado los recibos de este mes.
      </div>

      <div v-for="q in [1, 2]" :key="q" v-show="porQuincena(q).length" class="mb-3 last:mb-0">
        <div class="text-xs font-bold text-mifi-navy/40 uppercase mb-1">Quincena {{ q }}</div>
        <div v-for="r in porQuincena(q)" :key="r.id"
             class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
          <div class="flex items-center gap-2 min-w-0">
            <!-- Toggle pagado -->
            <button @click="togglePagado(r)" :title="r.estado === 'PAGADO' ? 'Marcar pendiente' : 'Marcar pagado'"
                    class="w-5 h-5 flex-shrink-0 rounded-full border-none cursor-pointer flex items-center justify-center transition-colors"
                    :class="r.estado === 'PAGADO' ? 'bg-mifi-green text-white' : 'bg-mifi-navy/10 text-transparent hover:bg-mifi-navy/20'">
              <i class="pi pi-check text-[10px]" :class="{ 'check-pop': r._justPaid }"></i>
            </button>
            <!-- Congelar -->
            <button @click="toggleCongelado(r)" title="Congelar (bolsillo)"
                    class="text-xs border-none bg-transparent cursor-pointer"
                    :class="r.estado === 'CONGELADO' ? 'text-mifi-cyan' : 'text-mifi-navy/20 hover:text-mifi-cyan'">
              <i class="pi pi-lock" v-if="r.estado === 'CONGELADO'"></i>
              <i class="pi pi-snowflake" v-else></i>
            </button>
            <span class="text-xs truncate" :class="r.estado === 'PAGADO' ? 'text-mifi-navy/40 line-through' : 'text-mifi-navy'">{{ r.nombre }}</span>
          </div>
          <span class="text-xs font-bold flex-shrink-0" :class="estadoColor(r.estado)">${{ fmt(r.monto) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { apiClient } from '../api/client';

const resumen = ref<any>({});
const recibos = ref<any[]>([]);
const loading = ref(false);

const fmt = (n: number) => Number(n || 0).toLocaleString('es-CO');
const porQuincena = (q: number) => recibos.value.filter(r => r.quincena === q);

const semaforoLabel = computed(() => ({ verde: 'Al día', amarillo: 'Justo', rojo: 'En riesgo' } as any)[resumen.value.semaforo] || 'Al día');
const semaforoDot = computed(() => ({ verde: 'bg-mifi-green', amarillo: 'bg-amber-500', rojo: 'bg-mifi-red' } as any)[resumen.value.semaforo] || 'bg-mifi-navy/20');
const semaforoGlow = computed(() => ({ verde: 'rgba(16,185,129,0.18)', amarillo: 'rgba(245,158,11,0.18)', rojo: 'rgba(239,68,68,0.18)' } as any)[resumen.value.semaforo] || 'rgba(15,23,42,0.08)');
const semaforoText = computed(() => ({ verde: 'text-mifi-green', amarillo: 'text-amber-600', rojo: 'text-mifi-red' } as any)[resumen.value.semaforo] || 'text-mifi-navy');
const estadoColor = (e: string) => e === 'PAGADO' ? 'text-mifi-green' : e === 'CONGELADO' ? 'text-mifi-cyan' : 'text-mifi-navy';
const esDiaDisparo = computed(() =>
  new Date().getDate() >= (resumen.value.dia_disparo || 28) && (resumen.value.flujo_libre_ajustado || 0) > 0);

const load = async () => {
  try {
    const [res, rec] = await Promise.all([
      apiClient.get('/ciclo/resumen'),
      apiClient.get('/ciclo/recibos'),
    ]);
    resumen.value = res.data;
    recibos.value = rec.data;
  } catch { /* backend puede estar arrancando */ }
};

const generar = async () => {
  loading.value = true;
  try { await apiClient.post('/ciclo/generar', {}); await load(); }
  finally { loading.value = false; }
};

const setEstado = async (r: any, estado: string, crearTxn = false) => {
  const prev = r.estado;
  r.estado = estado; // optimista
  if (estado === 'PAGADO') r._justPaid = true;
  try {
    await apiClient.patch(`/ciclo/recibos/${r.id}`, { estado, crear_transaccion: crearTxn });
    await load(); // refrescar resumen (semáforo/flujo cambian)
  } catch { r.estado = prev; }
};

const togglePagado = (r: any) =>
  setEstado(r, r.estado === 'PAGADO' ? 'PENDIENTE' : 'PAGADO', r.estado !== 'PAGADO');
const toggleCongelado = (r: any) =>
  setEstado(r, r.estado === 'CONGELADO' ? 'PENDIENTE' : 'CONGELADO');

defineExpose({ reload: load });
onMounted(load);
</script>

<style scoped>
/* ui-skills transitions-dev — success check (ligero) al marcar pagado */
@keyframes check-pop {
  0% { transform: scale(0.2) rotate(-80deg); opacity: 0; }
  60% { transform: scale(1.2) rotate(0); opacity: 1; }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}
.check-pop { animation: check-pop 450ms cubic-bezier(0.34, 1.45, 0.64, 1); }
@media (prefers-reduced-motion: reduce) { .check-pop { animation: none; } }
</style>
