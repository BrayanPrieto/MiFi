<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-mifi-navy m-0">Dashboard</h1>
        <p class="text-sm text-mifi-navy/50 mt-1">Resumen de tus finanzas — {{ mesLabel }}</p>
      </div>
      <div class="text-sm text-mifi-navy/40">{{ new Date().toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}</div>
    </div>

    <!-- Main layout: Chat LEFT + Métricas RIGHT -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">

      <!-- LEFT: AI Chat (2 cols) -->
      <div class="lg:col-span-2 space-y-4">
        <div class="glass-card p-5 h-full flex flex-col">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-mifi-cyan to-mifi-green flex items-center justify-center">
              <i class="pi pi-sparkles text-white text-sm"></i>
            </div>
            <div class="flex-1">
              <h3 class="text-sm font-bold text-mifi-navy m-0">Asistente IA</h3>
            </div>
          </div>

          <!-- Mode selector -->
          <div class="flex flex-wrap gap-1.5 mb-3">
            <button
              v-for="m in modes" :key="m.value"
              @click="selectedMode = m.value"
              class="px-2.5 py-1 rounded-full text-xs font-medium border transition-all cursor-pointer"
              :class="selectedMode === m.value
                ? 'bg-mifi-cyan text-white border-mifi-cyan'
                : 'bg-white text-mifi-navy/60 border-mifi-navy/10 hover:border-mifi-cyan/40'"
            >{{ m.icon }} {{ m.label }}</button>
          </div>

          <!-- Chat container -->
          <div ref="chatContainer" class="flex-1 bg-white/50 rounded-xl p-3 mb-3 min-h-[220px] max-h-[340px] overflow-y-auto border border-white/60">
            <div v-if="chatMessages.length === 0" class="flex flex-col items-center justify-center h-full text-mifi-navy/30 py-8 text-center">
              <i class="pi pi-sparkles text-2xl mb-2"></i>
              <p class="text-xs m-0">{{ modePlaceholder }}</p>
            </div>
            <div v-for="(msg, idx) in chatMessages" :key="idx" class="mb-2">
              <div :class="msg.role === 'user' ? 'text-right' : 'text-left'">
                <span class="inline-block px-3 py-2 rounded-xl text-sm max-w-[90%]" :class="msg.role === 'user' ? 'bg-mifi-cyan text-white' : 'bg-white border border-mifi-navy/10 text-mifi-navy'">
                  {{ msg.content }}
                </span>
                <span v-if="msg.saved" class="block text-xs text-mifi-green mt-0.5">💾 Registrado</span>
              </div>
            </div>
            <div v-if="aiLoading" class="text-left">
              <span class="inline-block px-3 py-2 rounded-xl text-xs bg-white border border-mifi-navy/10 text-mifi-navy/50">
                <i class="pi pi-spin pi-spinner mr-1"></i> Procesando...
              </span>
            </div>
          </div>

          <div class="flex gap-2">
            <InputText v-model="aiPrompt" :placeholder="modePlaceholder" class="flex-1 text-sm" @keyup.enter="sendAiMessage" />
            <Button
              :icon="isListening ? 'pi pi-stop' : 'pi pi-microphone'"
              @click="toggleVoice"
              :class="isListening ? '!bg-red-500 !border-none !text-white animate-pulse' : '!bg-mifi-cyan !border-none !text-white'"
              :title="isListening ? 'Detener grabación' : 'Hablar con micrófono'"
            />
            <Button icon="pi pi-send" :loading="aiLoading" @click="sendAiMessage" class="!bg-mifi-cyan !border-none !text-white" />
          </div>
        </div>
      </div>

      <!-- RIGHT: Métricas (3 cols) -->
      <div class="lg:col-span-3 space-y-4">
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 gap-3">
          <div class="glass-card p-4">
            <div class="flex items-center justify-between mb-1"><span class="text-xs font-medium text-mifi-navy/50">Ingresos</span><i class="pi pi-arrow-up text-mifi-green text-xs"></i></div>
            <span class="text-lg font-bold text-mifi-green">${{ fmt(data.ingresos) }}</span>
          </div>
          <div class="glass-card p-4">
            <div class="flex items-center justify-between mb-1"><span class="text-xs font-medium text-mifi-navy/50">Gastos</span><i class="pi pi-arrow-down text-mifi-red text-xs"></i></div>
            <span class="text-lg font-bold text-mifi-red">${{ fmt(data.total_gastos) }}</span>
          </div>
          <div class="glass-card p-4">
            <div class="flex items-center justify-between mb-1"><span class="text-xs font-medium text-mifi-navy/50">Balance</span><i class="pi pi-chart-line text-mifi-cyan text-xs"></i></div>
            <span class="text-lg font-bold" :class="data.balance >= 0 ? 'text-mifi-green' : 'text-mifi-red'">${{ fmt(data.balance) }}</span>
          </div>
          <div class="glass-card p-4">
            <div class="flex items-center justify-between mb-1"><span class="text-xs font-medium text-mifi-navy/50">Ahorro</span><i class="pi pi-percentage text-amber-500 text-xs"></i></div>
            <span class="text-lg font-bold text-amber-600">{{ data.ingresos > 0 ? Math.round((data.balance / data.ingresos) * 100) : 0 }}%</span>
          </div>
        </div>

        <!-- Desglose gastos: Pie + Leyenda -->
        <div class="glass-card p-4">
          <h4 class="text-xs font-bold text-mifi-navy/60 m-0 mb-3">DESGLOSE DE GASTOS</h4>
          <div class="flex items-center gap-5">
            <!-- CSS Pie Chart -->
            <div class="relative w-28 h-28 rounded-full flex-shrink-0" :style="{ background: pieGradient }">
              <div class="absolute inset-3 rounded-full bg-white/90 flex items-center justify-center flex-col">
                <span class="text-xs text-mifi-navy/50">Total</span>
                <span class="text-sm font-bold text-mifi-navy">${{ fmt(data.total_gastos) }}</span>
              </div>
            </div>
            <!-- Legend -->
            <div class="flex-1 space-y-2">
              <div>
                <div class="flex justify-between text-xs mb-0.5"><span class="text-mifi-navy/60">🔴 Fijos</span><span class="font-bold text-mifi-red">${{ fmt(data.gastos_fijos) }}</span></div>
                <div class="h-1.5 bg-mifi-navy/5 rounded-full overflow-hidden"><div class="h-full bg-mifi-red rounded-full" :style="{ width: barPct(data.gastos_fijos, data.total_gastos) + '%' }"></div></div>
              </div>
              <div>
                <div class="flex justify-between text-xs mb-0.5"><span class="text-mifi-navy/60">🟠 Variables</span><span class="font-bold text-orange-500">${{ fmt(data.gastos_variables) }}</span></div>
                <div class="h-1.5 bg-mifi-navy/5 rounded-full overflow-hidden"><div class="h-full bg-orange-500 rounded-full" :style="{ width: barPct(data.gastos_variables, data.total_gastos) + '%' }"></div></div>
              </div>
              <div>
                <div class="flex justify-between text-xs mb-0.5"><span class="text-mifi-navy/60">🟣 Préstamos</span><span class="font-bold text-purple-500">${{ fmt(data.cuotas_prestamo) }}</span></div>
                <div class="h-1.5 bg-mifi-navy/5 rounded-full overflow-hidden"><div class="h-full bg-purple-500 rounded-full" :style="{ width: barPct(data.cuotas_prestamo, data.total_gastos) + '%' }"></div></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tarjetas de crédito -->
        <div class="glass-card p-4" v-if="data.tarjetas.length > 0">
          <h4 class="text-xs font-bold text-mifi-navy/60 m-0 mb-3">TARJETAS DE CRÉDITO</h4>
          <div v-for="t in data.tarjetas" :key="t.id" class="mb-3 last:mb-0">
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-mifi-navy">{{ t.nombre }}</span>
              <span class="text-mifi-navy/40">${{ fmt(t.consumido) }} / ${{ fmt(t.cupo_total) }}</span>
            </div>
            <div class="h-3 bg-mifi-navy/5 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all" :class="t.porcentaje_usado > 80 ? 'bg-mifi-red' : t.porcentaje_usado > 50 ? 'bg-amber-500' : 'bg-purple-500'" :style="{ width: t.porcentaje_usado + '%' }"></div>
            </div>
            <div class="flex justify-between text-xs mt-0.5">
              <span :class="t.porcentaje_usado > 80 ? 'text-mifi-red' : 'text-mifi-navy/40'">{{ t.porcentaje_usado }}% usado</span>
              <span class="text-mifi-green">${{ fmt(t.cupo_disponible) }} libre</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom row: Recurrentes + Cuentas + Movimientos -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Recurrentes -->
      <div class="glass-card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-mifi-navy m-0"><i class="pi pi-sync text-mifi-cyan mr-2"></i>Recurrentes</h3>
          <router-link to="/recurrents" class="text-xs text-mifi-cyan font-medium no-underline hover:underline">Gestionar</router-link>
        </div>
        <div class="max-h-[250px] overflow-y-auto">
          <div v-if="data.recurrentes.length === 0" class="text-center py-3 text-mifi-navy/30 text-xs">Sin recurrentes</div>
          <div v-for="r in data.recurrentes" :key="r.id" class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
            <div class="flex items-center gap-2">
              <i :class="r.pagado ? 'pi pi-check-circle text-mifi-green' : 'pi pi-clock text-amber-500'" class="text-xs"></i>
              <span class="text-xs text-mifi-navy truncate max-w-[120px]">{{ r.nombre }}</span>
            </div>
            <span class="text-xs font-bold" :class="r.tipo === 'INGRESO' ? 'text-mifi-green' : 'text-mifi-red'">{{ r.tipo === 'INGRESO' ? '+' : '-' }}${{ Number(r.monto).toLocaleString('es-CO') }}</span>
          </div>
        </div>
      </div>

      <!-- Cuentas -->
      <div class="glass-card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-mifi-navy m-0"><i class="pi pi-wallet text-mifi-cyan mr-2"></i>Tus Cuentas</h3>
          <router-link to="/accounts" class="text-xs text-mifi-cyan font-medium no-underline hover:underline">Gestionar</router-link>
        </div>
        <div class="max-h-[250px] overflow-y-auto">
          <div v-for="c in data.cuentas" :key="c.id" class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
            <span class="text-xs text-mifi-navy truncate max-w-[120px]">{{ c.nombre }}</span>
            <span class="text-xs font-bold" :class="c.saldo >= 0 ? 'text-mifi-green' : 'text-mifi-red'">${{ Number(c.saldo).toLocaleString('es-CO') }}</span>
          </div>
          <div v-if="data.cuentas.length === 0" class="text-center py-3 text-mifi-navy/30 text-xs">Sin cuentas</div>
        </div>
      </div>

      <!-- Movimientos del Mes: Ingresos y Gastos -->
      <div class="glass-card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-mifi-navy m-0"><i class="pi pi-arrows-v text-mifi-cyan mr-2"></i>Movimientos</h3>
          <router-link to="/transactions" class="text-xs text-mifi-cyan font-medium no-underline hover:underline">Ver todo</router-link>
        </div>
        <div class="max-h-[250px] overflow-y-auto">
          <div v-if="!data.ultimas_transacciones || data.ultimas_transacciones.length === 0" class="text-center py-3 text-mifi-navy/30 text-xs">Sin movimientos este mes</div>
          <div v-for="t in (data.ultimas_transacciones || [])" :key="t.id" class="flex items-center justify-between py-2 border-b border-mifi-navy/5 last:border-0">
            <div class="flex items-center gap-2">
              <i :class="t.tipo === 'INGRESO' ? 'pi pi-arrow-up text-mifi-green' : 'pi pi-arrow-down text-mifi-red'" class="text-xs"></i>
              <span class="text-xs text-mifi-navy truncate max-w-[120px]">{{ t.descripcion || 'Sin descripción' }}</span>
            </div>
            <span class="text-xs font-bold" :class="t.tipo === 'INGRESO' ? 'text-mifi-green' : 'text-mifi-red'">{{ t.tipo === 'INGRESO' ? '+' : '-' }}${{ Number(t.monto).toLocaleString('es-CO') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { apiClient } from '../api/client';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';

const data = ref<any>({
  ingresos: 0, gastos_fijos: 0, gastos_variables: 0, cuotas_prestamo: 0,
  ahorros: 0, total_gastos: 0, balance: 0, tarjetas: [], recurrentes: [], cuentas: [],
});

const modes = [
  { value: 'general', label: 'General', icon: '💬' },
  { value: 'transaccion', label: 'Transacción', icon: '💰' },
  { value: 'recurrente', label: 'Recurrente', icon: '🔄' },
  { value: 'prestamo', label: 'Préstamo', icon: '🏦' },
  { value: 'meta', label: 'Meta', icon: '🎯' },
  { value: 'categoria', label: 'Categoría', icon: '📁' },
];

const modePlaceholders: Record<string, string> = {
  general: '¿Cuánto me queda este mes? · ¿Ya pagué el arriendo?',
  transaccion: 'Pagué 50k gasolina · Me llegó la nómina',
  recurrente: 'Netflix $50k cada mes · Mi arriendo son 2 millones',
  prestamo: 'Debo 9.5M en Nu, cuota 1.5M · Avance de tarjeta 500k',
  meta: 'Quiero ahorrar 10M para una moto · Viaje a Europa $8M',
  categoria: 'Categoría "Suscripciones" · "Comida mascotas"',
};

const selectedMode = ref('general');
const chatMessages = ref<{ role: string; content: string; saved?: boolean }[]>([]);
const aiPrompt = ref('');
const aiLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

const modePlaceholder = computed(() => modePlaceholders[selectedMode.value] || '');
const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
const mesLabel = meses[new Date().getMonth()] + ' ' + new Date().getFullYear();

const fmt = (n: number) => Number(n || 0).toLocaleString('es-CO');
const barPct = (part: number, total: number) => total > 0 ? Math.min(100, Math.round((part / total) * 100)) : 0;

const pieGradient = computed(() => {
  const total = data.value.total_gastos || 1;
  const p1 = (data.value.gastos_fijos / total) * 100;
  const p2 = p1 + (data.value.gastos_variables / total) * 100;
  if (total <= 0) return 'conic-gradient(#e2e8f0 0% 100%)';
  return `conic-gradient(#ef4444 0% ${p1}%, #f97316 ${p1}% ${p2}%, #a855f7 ${p2}% 100%)`;
});

const loadData = async () => {
  try { data.value = (await apiClient.get('/dashboard/resumen-mensual')).data; } catch { /* empty */ }
};

onMounted(loadData);

const scrollChat = () => nextTick(() => { if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight; });

const sendAiMessage = async () => {
  if (!aiPrompt.value.trim()) return;
  const userMsg = aiPrompt.value;
  chatMessages.value.push({ role: 'user', content: userMsg });
  aiPrompt.value = '';
  aiLoading.value = true;
  scrollChat();

  try {
    const history = chatMessages.value.slice(-10).map(m => ({ role: m.role, content: m.content }));
    const res = await apiClient.post('/ia/parse', {
      text: userMsg,
      mode: selectedMode.value,
      history,
    });
    chatMessages.value.push({ role: 'assistant', content: res.data.reply || 'Respuesta recibida.', saved: res.data.saved || false });
    if (res.data.saved) await loadData();
  } catch {
    chatMessages.value.push({ role: 'assistant', content: '⚠️ No pude conectar con la IA.' });
  } finally {
    aiLoading.value = false;
    scrollChat();
  }
};
const isListening = ref(false);
let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];

const toggleVoice = async () => {
  // Si ya está grabando, detener
  if (isListening.value && mediaRecorder) {
    mediaRecorder.stop();
    return;
  }

  // Pedir permiso de micrófono
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      isListening.value = false;
      stream.getTracks().forEach(t => t.stop()); // Liberar micrófono

      if (audioChunks.length === 0) return;

      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      try {
        chatMessages.value.push({ role: 'assistant', content: '🎤 Transcribiendo audio...' });
        scrollChat();
        const res = await apiClient.post('/ia/transcribe', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        chatMessages.value.pop(); // Quitar "Transcribiendo..."
        if (res.data.text) {
          aiPrompt.value = res.data.text;
        }
      } catch {
        chatMessages.value.pop();
        chatMessages.value.push({ role: 'assistant', content: '⚠️ Error al transcribir. Intenta de nuevo.' });
        scrollChat();
      }
    };

    mediaRecorder.start();
    isListening.value = true;
  } catch (err) {
    chatMessages.value.push({ role: 'assistant', content: '⚠️ No se pudo acceder al micrófono. Verifica permisos.' });
    scrollChat();
  }
};
</script>
