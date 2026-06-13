import React from 'react';
import ReactDOM from 'react-dom/client';
import PasswordsView from './pages/PasswordsView';

// Entry standalone solo per sviluppo isolato.
// In produzione il componente viene caricato come remote dal host (small-cmr-base).
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <PasswordsView />
  </React.StrictMode>
);
