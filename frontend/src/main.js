// Standalone dev/preview entry. In production the PasswordsView is loaded
// as a federated remote inside small-cmr-base.
import { createApp, h } from 'vue';
import { NConfigProvider, NMessageProvider, NDialogProvider, itIT, dateItIT } from 'naive-ui';
import PasswordsView from './pages/PasswordsView.vue';

const App = {
  render() {
    return h(NConfigProvider, { locale: itIT, dateLocale: dateItIT }, () =>
      h(NDialogProvider, null, () =>
        h(NMessageProvider, null, () => h(PasswordsView))
      )
    );
  },
};

createApp(App).mount('#app');
