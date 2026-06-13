<script setup>
import { ref, reactive } from 'vue';
import {
  NModal, NCard, NInput, NButton, NSpace, NFormItem, NAlert, NInputGroup,
  useMessage,
} from 'naive-ui';
import api from '../api/client';

const props = defineProps({
  mode: { type: String, required: true },     // 'create' | 'edit'
  model: { type: Object, required: true },
});
const emit = defineEmits(['close', 'saved']);
const msg = useMessage();

const form = reactive({
  service: props.model?.service || '',
  account_username: props.model?.account_username || '',
  url: props.model?.url || '',
  description: props.model?.description || '',
  password: '',
});
const showPwd = ref(false);
const busy = ref(false);
const error = ref(null);

const generate = (len = 20) => {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  form.password = Array.from(arr, n => charset[n % charset.length]).join('');
  showPwd.value = true;
};

const submit = async () => {
  busy.value = true;
  error.value = null;
  try {
    if (props.mode === 'create') {
      await api.post('/api/passwords', form);
      msg.success('Password creata');
    } else {
      const payload = { ...form };
      if (!payload.password) delete payload.password;
      await api.put(`/api/passwords/${props.model.id}`, payload);
      msg.success('Password aggiornata');
    }
    emit('saved');
  } catch (e) {
    error.value = e.response?.data?.detail || 'Salvataggio fallito';
  } finally {
    busy.value = false;
  }
};
</script>

<template>
  <NModal :show="true" :mask-closable="false" @update:show="(v) => !v && emit('close')">
    <NCard :title="mode === 'create' ? 'Nuova password' : 'Modifica password'"
           style="max-width: 560px;" closable @close="emit('close')">
      <NFormItem label="Servizio *">
        <NInput v-model:value="form.service" placeholder="es. Gmail, AWS console" />
      </NFormItem>
      <NFormItem label="Utente *">
        <NInput v-model:value="form.account_username" placeholder="es. mario@gmail.com" />
      </NFormItem>
      <NFormItem :label="`Password ${mode === 'edit' ? '(lasciare vuoto per non modificare)' : '*'}`">
        <NInputGroup>
          <NInput v-model:value="form.password"
                  :type="showPwd ? 'text' : 'password'"
                  placeholder="••••••••" />
          <NButton @click="showPwd = !showPwd">{{ showPwd ? 'Nascondi' : 'Mostra' }}</NButton>
          <NButton @click="generate()">Genera</NButton>
        </NInputGroup>
      </NFormItem>
      <NFormItem label="URL">
        <NInput v-model:value="form.url" placeholder="https://" />
      </NFormItem>
      <NFormItem label="Descrizione">
        <NInput v-model:value="form.description" type="textarea"
                :autosize="{ minRows: 2, maxRows: 4 }"
                placeholder="es. account amministratore di produzione" />
      </NFormItem>
      <NAlert v-if="error" type="error" :show-icon="false" style="margin-bottom: 12px;">{{ error }}</NAlert>
      <NSpace justify="end">
        <NButton @click="emit('close')">Annulla</NButton>
        <NButton type="primary" :loading="busy"
                 :disabled="!form.service || !form.account_username || (mode === 'create' && !form.password)"
                 @click="submit">
          {{ busy ? 'Salvataggio...' : 'Salva' }}
        </NButton>
      </NSpace>
    </NCard>
  </NModal>
</template>
