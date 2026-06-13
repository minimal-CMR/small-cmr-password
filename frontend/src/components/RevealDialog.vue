<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { NModal, NCard, NInput, NButton, NSpace, NInputGroup, useMessage } from 'naive-ui';

const props = defineProps({
  item: { type: Object, required: true },  // { service, account, password }
});
const emit = defineEmits(['close']);
const msg = useMessage();

const show = ref(false);
const countdown = ref(30);
let timer = null;

onMounted(() => {
  timer = setInterval(() => {
    countdown.value -= 1;
    if (countdown.value <= 0) emit('close');
  }, 1000);
});
onBeforeUnmount(() => { if (timer) clearInterval(timer); });

const copy = async () => {
  try {
    await navigator.clipboard.writeText(props.item.password);
    msg.success('Password copiata');
  } catch {
    msg.error('Copia fallita');
  }
};
</script>

<template>
  <NModal :show="true" :mask-closable="true" @update:show="(v) => !v && emit('close')">
    <NCard :title="item.service" style="max-width: 440px;" closable @close="emit('close')">
      <p style="color: #666; margin-bottom: 16px;">{{ item.account }}</p>
      <NInputGroup>
        <NInput :value="item.password" readonly
                :type="show ? 'text' : 'password'"
                style="font-family: monospace;" />
        <NButton @click="show = !show">{{ show ? 'Nascondi' : 'Mostra' }}</NButton>
        <NButton type="primary" @click="copy">Copia</NButton>
      </NInputGroup>
      <p style="font-size: 0.85em; color: #999; margin-top: 12px;">
        Chiusura automatica tra {{ countdown }}s
      </p>
      <NSpace justify="end" style="margin-top: 16px;">
        <NButton @click="emit('close')">Chiudi</NButton>
      </NSpace>
    </NCard>
  </NModal>
</template>
