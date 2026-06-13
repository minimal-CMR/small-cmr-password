import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'password_module',
      filename: 'remoteEntry.js',
      exposes: {
        './PasswordsView': './src/pages/PasswordsView.vue',
      },
      shared: ['vue', 'axios'],
    }),
  ],
  server: {
    port: 5176,
    proxy: {
      '/api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5176,
    strictPort: true,
  },
  build: {
    modulePreload: false,
    target: 'esnext',
    minify: false,
    cssCodeSplit: false,
  },
});
