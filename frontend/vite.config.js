import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'password_module',
      filename: 'remoteEntry.js',
      exposes: {
        './PasswordsView': './src/pages/PasswordsView.jsx',
      },
      shared: ['react', 'react-dom', 'react-router-dom', 'axios'],
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
