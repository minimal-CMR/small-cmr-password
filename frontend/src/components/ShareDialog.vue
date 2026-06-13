<script setup>
import { ref, computed, onMounted, h } from 'vue';
import {
  NModal, NCard, NInput, NSelect, NButton, NSpace, NCheckbox,
  NScrollbar, NAlert, useMessage, useDialog,
} from 'naive-ui';
import api from '../api/client';

const props = defineProps({
  password: { type: Object, required: true },
  me: { type: Object, default: null },
});
const emit = defineEmits(['close', 'updated']);
const msg = useMessage();
const dlg = useDialog();

const users = ref([]);
const ditte = ref([]);
const teams = ref([]);
const perms = ref(new Map());     // userId -> 'read' | 'write'
const original = ref(new Set());  // userIds shared at load

const fNome = ref('');
const fCognome = ref('');
const fDitta = ref(null);
const fTeam = ref(null);

const busy = ref(false);
const error = ref(null);

onMounted(async () => {
  try {
    const [u, d, t, shares] = await Promise.all([
      api.get('/api/users'),
      api.get('/api/ditte').catch(() => ({ data: [] })),
      api.get('/api/teams').catch(() => ({ data: [] })),
      api.get(`/api/passwords/${props.password.id}/shares`),
    ]);
    users.value = u.data.filter(x => x.id !== props.me?.id && x.id !== props.password.owner.id);
    ditte.value = d.data;
    teams.value = t.data;
    const m = new Map();
    const s = new Set();
    shares.data.forEach(sh => { m.set(sh.recipient.id, sh.permission); s.add(sh.recipient.id); });
    perms.value = m;
    original.value = s;
  } catch (e) {
    error.value = e.response?.data?.detail || 'Errore caricamento';
  }
});

const dittaOptions = computed(() => [
  { label: 'Tutte', value: null },
  ...ditte.value.map(d => ({ label: d.nome, value: d.id })),
]);
const teamOptions = computed(() => [
  { label: 'Tutti', value: null },
  ...teams.value.map(t => ({ label: `${t.name} (${(t.members || []).length})`, value: t.id })),
]);

const teamMemberIds = computed(() => {
  if (!fTeam.value) return null;
  return new Set((teams.value.find(t => t.id === fTeam.value)?.members || []).map(m => m.id));
});

const visibleUsers = computed(() => users.value.filter(u => {
  if (fNome.value.trim() && !(u.nome || '').toLowerCase().includes(fNome.value.trim().toLowerCase())) return false;
  if (fCognome.value.trim() && !(u.cognome || '').toLowerCase().includes(fCognome.value.trim().toLowerCase())) return false;
  if (fDitta.value && u.ditta_id !== fDitta.value) return false;
  if (teamMemberIds.value && !teamMemberIds.value.has(u.id)) return false;
  return true;
}));

const toggleUser = (uid) => {
  const next = new Map(perms.value);
  if (next.has(uid)) next.delete(uid);
  else next.set(uid, 'read');
  perms.value = next;
};

const setPermission = (uid, perm) => {
  const next = new Map(perms.value);
  next.set(uid, perm);
  perms.value = next;
};

const selectAll = () => {
  const next = new Map(perms.value);
  visibleUsers.value.forEach(u => { if (!next.has(u.id)) next.set(u.id, 'read'); });
  perms.value = next;
};
const deselectAll = () => {
  const next = new Map(perms.value);
  visibleUsers.value.forEach(u => next.delete(u.id));
  perms.value = next;
};

const shareTeam = () => {
  if (!fTeam.value) return;
  dlg.warning({
    title: 'Condividere con tutto il team?',
    content: 'Tutti i membri del team selezionato riceveranno permesso di lettura.',
    positiveText: 'Condividi', negativeText: 'Annulla',
    onPositiveClick: async () => {
      try {
        await api.post(`/api/passwords/${props.password.id}/shares/team/${fTeam.value}?permission=read`);
        msg.success('Condiviso con team');
        emit('updated'); emit('close');
      } catch (e) {
        error.value = e.response?.data?.detail || 'Condivisione team fallita';
      }
    },
  });
};
const shareDitta = () => {
  if (!fDitta.value) return;
  dlg.warning({
    title: 'Condividere con tutta la ditta?',
    content: 'Tutti gli utenti della ditta selezionata riceveranno permesso di lettura.',
    positiveText: 'Condividi', negativeText: 'Annulla',
    onPositiveClick: async () => {
      try {
        await api.post(`/api/passwords/${props.password.id}/shares/ditta/${fDitta.value}?permission=read`);
        msg.success('Condiviso con ditta');
        emit('updated'); emit('close');
      } catch (e) {
        error.value = e.response?.data?.detail || 'Condivisione ditta fallita';
      }
    },
  });
};

const save = async () => {
  busy.value = true; error.value = null;
  try {
    const recipients = Array.from(perms.value.entries()).map(([user_id, permission]) => ({ user_id, permission }));
    if (recipients.length) {
      await api.post(`/api/passwords/${props.password.id}/shares`, { recipients });
    }
    const toRevoke = [...original.value].filter(id => !perms.value.has(id));
    await Promise.all(toRevoke.map(id => api.delete(`/api/passwords/${props.password.id}/shares/${id}`)));
    msg.success('Condivisioni aggiornate');
    emit('updated'); emit('close');
  } catch (e) {
    error.value = e.response?.data?.detail || 'Errore di condivisione';
  } finally {
    busy.value = false;
  }
};
</script>

<template>
  <NModal :show="true" :mask-closable="false" @update:show="(v) => !v && emit('close')">
    <NCard title="Condividi password" style="max-width: 720px;" closable @close="emit('close')">
      <p style="color: #666; margin-bottom: 16px;">
        {{ password.service }} — {{ password.account_username }}
      </p>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; margin-bottom: 12px;">
        <NInput v-model:value="fNome" placeholder="Nome" clearable />
        <NInput v-model:value="fCognome" placeholder="Cognome" clearable />
        <NSelect v-model:value="fDitta" :options="dittaOptions" placeholder="Ditta" clearable />
        <NSelect v-model:value="fTeam" :options="teamOptions" placeholder="Team" clearable />
      </div>

      <NSpace v-if="fDitta || fTeam" style="margin-bottom: 12px;">
        <NButton v-if="fTeam" size="small" @click="shareTeam">Condividi con team intero</NButton>
        <NButton v-if="fDitta" size="small" @click="shareDitta">Condividi con ditta intera</NButton>
      </NSpace>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 0.9em;">
        <span><strong>Utenti</strong>
          <span style="color: #999; margin-left: 6px;">({{ perms.size }} selezionati di {{ visibleUsers.length }})</span>
        </span>
        <NSpace size="small">
          <NButton size="tiny" text @click="selectAll">Tutti</NButton>
          <NButton size="tiny" text @click="deselectAll">Nessuno</NButton>
        </NSpace>
      </div>

      <NScrollbar style="border: 1px solid #ddd; border-radius: 6px; max-height: 280px; min-height: 160px;">
        <div v-if="visibleUsers.length === 0" style="padding: 16px; text-align: center; color: #999; font-size: 0.9em;">
          Nessun utente trovato
        </div>
        <div v-for="u in visibleUsers" :key="u.id"
             style="display: flex; align-items: center; gap: 12px; padding: 6px 12px; border-bottom: 1px solid #f0f0f0;">
          <NCheckbox :checked="perms.has(u.id)" @update:checked="toggleUser(u.id)" />
          <div style="flex: 1; min-width: 0;">
            <div style="font-size: 0.9em; font-weight: 500;">{{ u.nome }} {{ u.cognome }}</div>
            <div style="font-size: 0.78em; color: #999;">{{ u.email }}</div>
          </div>
          <NSpace v-if="perms.has(u.id)" :wrap="false" :size="0">
            <NButton size="tiny" :type="perms.get(u.id) === 'read' ? 'primary' : 'default'"
                     @click="setPermission(u.id, 'read')">Vista</NButton>
            <NButton size="tiny" :type="perms.get(u.id) === 'write' ? 'warning' : 'default'"
                     @click="setPermission(u.id, 'write')">Modifica</NButton>
          </NSpace>
          <span v-else style="color: #ccc; font-size: 0.75em; width: 90px; text-align: right;">—</span>
        </div>
      </NScrollbar>

      <NAlert v-if="error" type="error" :show-icon="false" style="margin-top: 12px;">{{ error }}</NAlert>

      <NSpace justify="end" style="margin-top: 16px;">
        <NButton @click="emit('close')">Chiudi</NButton>
        <NButton type="primary" :loading="busy" @click="save">
          {{ busy ? 'Salvataggio...' : 'Salva' }}
        </NButton>
      </NSpace>
    </NCard>
  </NModal>
</template>
