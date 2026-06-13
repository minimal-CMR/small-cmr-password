<script setup>
import { ref } from 'vue';
import { NModal, NCard, NInput, NButton, NSpace, NAlert } from 'naive-ui';

const props = defineProps({
  title: { type: String, default: 'Conferma identita\'' },
  description: { type: String, default: 'Inserisci la tua password.' },
  submitLabel: { type: String, default: 'Conferma' },
  error: { type: String, default: null },
});
const emit = defineEmits(['confirmed', 'cancel']);

const pwd = ref('');
const busy = ref(false);

const submit = async () => {
  if (!pwd.value) return;
  busy.value = true;
  try { await emit('confirmed', pwd.value); }
  finally { busy.value = false; }
};
</script>

<template>
  <NModal :show="true" :mask-closable="true" @update:show="(v) => !v && emit('cancel')">
    <NCard :title="title" style="max-width: 420px;" closable @close="emit('cancel')">
      <p style="color: #666; font-size: 0.9em; margin-bottom: 16px;">{{ description }}</p>
      <NAlert v-if="error" type="error" :show-icon="false" style="margin-bottom: 12px;">{{ error }}</NAlert>
      <NInput v-model:value="pwd" type="password" placeholder="••••••••"
              autofocus show-password-on="click"
              @keyup.enter="submit" />
      <NSpace justify="end" style="margin-top: 16px;">
        <NButton @click="emit('cancel')">Annulla</NButton>
        <NButton type="primary" :loading="busy" :disabled="!pwd" @click="submit">
          {{ busy ? 'Verifica...' : submitLabel }}
        </NButton>
      </NSpace>
    </NCard>
  </NModal>
</template>
