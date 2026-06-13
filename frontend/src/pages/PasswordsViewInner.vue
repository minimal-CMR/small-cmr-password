<script setup>
import { ref, computed, onMounted, h } from 'vue';
import {
  NCard, NInput, NCheckbox, NButton, NSpace, NTag, NDataTable,
  useMessage, useDialog,
} from 'naive-ui';
import api from '../api/client';
import PasswordDialog from '../components/PasswordDialog.vue';
import RevealDialog from '../components/RevealDialog.vue';
import ShareDialog from '../components/ShareDialog.vue';
import UnlockDialog from '../components/UnlockDialog.vue';

const msg = useMessage();
const dlg = useDialog();

const items = ref([]);
const loading = ref(false);
const me = ref(null);

const search = ref({
  account_username: '', service: '', description: '',
  owner_email: '', include_shared: true,
});

const passwordDlg = ref({ open: false, mode: 'create', model: null });
const shareDlg = ref({ open: false, password: null });
const revealDlg = ref({ open: false, item: null });
const confirmDlg = ref({ open: false, item: null, mode: 'reveal' });
const confirmError = ref(null);

const unlocked = ref(false);
const unlockDlgOpen = ref(true);
const unlockError = ref(null);

const isAdmin = computed(() => me.value?.ruoli?.includes('admin'));

const loadMe = async () => {
  try { me.value = (await api.get('/api/auth/me')).data; }
  catch { me.value = null; }
};

const loadList = async () => {
  loading.value = true;
  try {
    const params = {};
    Object.entries(search.value).forEach(([k, v]) => {
      if (v === '' || v === null || v === undefined) return;
      params[k] = v;
    });
    const { data } = await api.get('/api/passwords', { params });
    items.value = data;
  } catch (e) {
    msg.error(e.response?.data?.detail || 'Errore caricamento');
  } finally {
    loading.value = false;
  }
};

const tryUnlock = async (userPassword) => {
  unlockError.value = null;
  try {
    await api.post('/api/passwords/vault/unlock', { user_password: userPassword });
    unlocked.value = true;
    unlockDlgOpen.value = false;
    await loadList();
  } catch (e) {
    unlockError.value = e.response?.data?.detail || 'Password errata';
  }
};

const lockVault = () => {
  unlocked.value = false;
  items.value = [];
  unlockError.value = null;
  unlockDlgOpen.value = true;
};

const resetSearch = () => {
  search.value = { account_username: '', service: '', description: '', owner_email: '', include_shared: true };
  loadList();
};

onMounted(loadMe);

const canEdit = (p) => isAdmin.value || p.owner?.id === me.value?.id || p.my_permission === 'write';
const canShare = canEdit;

const openCreate = () => {
  passwordDlg.value = { open: true, mode: 'create',
    model: { account_username: '', service: '', description: '', url: '', password: '' } };
};
const openEdit = (p) => {
  passwordDlg.value = { open: true, mode: 'edit', model: { ...p, password: '' } };
};
const onSaved = () => {
  passwordDlg.value = { open: false, mode: 'create', model: null };
  loadList();
};

const remove = (p) => {
  dlg.warning({
    title: 'Eliminare la password?',
    content: `"${p.service}" (${p.account_username}) sara' eliminata.`,
    positiveText: 'Elimina', negativeText: 'Annulla',
    onPositiveClick: async () => {
      try { await api.delete(`/api/passwords/${p.id}`); msg.success('Password eliminata'); loadList(); }
      catch (e) { msg.error(e.response?.data?.detail || 'Eliminazione fallita'); }
    },
  });
};

const askThenReveal = (p) => { confirmDlg.value = { open: true, item: p, mode: 'reveal' }; confirmError.value = null; };
const askThenCopy = (p)   => { confirmDlg.value = { open: true, item: p, mode: 'copy'   }; confirmError.value = null; };

const onPasswordConfirmed = async (userPassword) => {
  const { item, mode } = confirmDlg.value;
  confirmError.value = null;
  try {
    const { data } = await api.post(`/api/passwords/${item.id}/reveal`, { user_password: userPassword });
    confirmDlg.value = { open: false, item: null, mode: 'reveal' };
    if (mode === 'copy') {
      await navigator.clipboard.writeText(data.password);
      msg.success('Password copiata negli appunti');
    } else {
      revealDlg.value = { open: true, item: { service: item.service, account: item.account_username, password: data.password } };
    }
  } catch (e) {
    confirmError.value = e.response?.data?.detail || 'Password vault errata o accesso non consentito';
  }
};

const columns = computed(() => [
  {
    title: 'Servizio', key: 'service',
    render: r => h('span', null, [
      h('strong', null, r.service),
      r.shared ? h(NTag, { type: 'info', size: 'small', round: true, style: 'margin-left: 6px;' }, () => 'condivisa') : null,
    ]),
  },
  { title: 'Utente', key: 'account_username' },
  { title: 'Descrizione', key: 'description', render: r => r.description || '—' },
  {
    title: 'Proprietario', key: 'owner',
    render: r => h('div', null, [
      h('div', null, `${r.owner?.nome || ''} ${r.owner?.cognome || ''}`.trim() || '—'),
      h('div', { style: 'font-size: 0.85em; color: #999;' }, r.owner?.email || ''),
    ]),
  },
  {
    title: 'Azioni', key: 'actions', width: 360,
    render: r => h(NSpace, { size: 'small' }, () => {
      const actions = [
        h(NButton, { size: 'small', onClick: () => askThenCopy(r) }, () => 'Copia'),
        h(NButton, { size: 'small', onClick: () => askThenReveal(r) }, () => 'Mostra'),
      ];
      if (canShare(r)) actions.push(
        h(NButton, { size: 'small', onClick: () => shareDlg.value = { open: true, password: r } }, () => 'Condividi'));
      if (canEdit(r)) {
        actions.push(h(NButton, { size: 'small', onClick: () => openEdit(r) }, () => 'Modifica'));
        actions.push(h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => remove(r) }, () => 'Elimina'));
      }
      return actions;
    }),
  },
]);
</script>

<template>
  <div class="page" style="padding: 28px 32px;">
    <template v-if="!unlocked">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">Le mie password</h1>
      </div>
      <NCard>
        <div style="padding: 32px; text-align: center; color: #666;">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">🔒</div>
          <p style="margin-bottom: 16px;">Vault bloccato. Inserisci la tua password per accedere.</p>
          <NButton type="primary" @click="() => { unlockError = null; unlockDlgOpen = true; }">
            Sblocca vault
          </NButton>
        </div>
      </NCard>
      <UnlockDialog v-if="unlockDlgOpen"
                    title="Sblocca il vault"
                    description="Inserisci la tua password per accedere all'elenco delle password salvate."
                    submit-label="Sblocca"
                    :error="unlockError"
                    @confirmed="tryUnlock"
                    @cancel="unlockDlgOpen = false" />
    </template>

    <template v-else>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">Le mie password</h1>
        <NSpace>
          <NButton @click="lockVault" title="Blocca il vault — sara' richiesta nuovamente la password">
            🔒 Blocca
          </NButton>
          <NButton type="primary" @click="openCreate">+ Nuova password</NButton>
        </NSpace>
      </div>

      <NCard title="Ricerca" style="margin-bottom: 20px;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
          <NInput v-model:value="search.account_username" placeholder="Utente (es. mario@gmail.com)" clearable />
          <NInput v-model:value="search.service" placeholder="Servizio (es. AWS, Gmail)" clearable />
          <NInput v-model:value="search.description" placeholder="Descrizione" clearable />
          <NInput v-if="isAdmin" v-model:value="search.owner_email" placeholder="Email proprietario" clearable />
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; flex-wrap: wrap; gap: 8px;">
          <NCheckbox v-model:checked="search.include_shared">Includi password condivise con me</NCheckbox>
          <NSpace>
            <NButton size="small" @click="resetSearch">Reset</NButton>
            <NButton size="small" type="primary" @click="loadList">Cerca</NButton>
          </NSpace>
        </div>
      </NCard>

      <NDataTable :columns="columns" :data="items" :loading="loading" :bordered="false" />

      <PasswordDialog v-if="passwordDlg.open"
                      :mode="passwordDlg.mode" :model="passwordDlg.model"
                      @close="passwordDlg.open = false" @saved="onSaved" />

      <ShareDialog v-if="shareDlg.open"
                   :password="shareDlg.password" :me="me"
                   @close="shareDlg.open = false"
                   @updated="loadList" />

      <RevealDialog v-if="revealDlg.open"
                    :item="revealDlg.item"
                    @close="revealDlg.open = false" />

      <UnlockDialog v-if="confirmDlg.open"
                    title="Conferma identita'"
                    description="Inserisci la tua password per visualizzare la password salvata."
                    submit-label="Conferma"
                    :error="confirmError"
                    @confirmed="onPasswordConfirmed"
                    @cancel="confirmDlg.open = false" />
    </template>
  </div>
</template>
