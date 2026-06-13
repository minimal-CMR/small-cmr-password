<script setup>
// Wrapper: monta i providers Naive UI cosi' il componente funziona
// sia standalone (npm run preview) sia come remote federato.
import { NConfigProvider, NMessageProvider, NDialogProvider, itIT, dateItIT } from 'naive-ui';
import PasswordsViewInner from './PasswordsViewInner.vue';
</script>

<template>
  <NConfigProvider :locale="itIT" :date-locale="dateItIT">
    <NDialogProvider>
      <NMessageProvider>
        <PasswordsViewInner />
      </NMessageProvider>
    </NDialogProvider>
  </NConfigProvider>
</template>
