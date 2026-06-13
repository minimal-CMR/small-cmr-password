import React, { useState } from 'react';
import api from '../api/client';

const overlayStyle = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16,
};

const modalStyle = {
  background: '#fff', borderRadius: 8, padding: 24,
  width: '100%', maxWidth: 540, boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
};

function generatePassword(len = 20) {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  return Array.from(arr, n => charset[n % charset.length]).join('');
}

export default function PasswordDialog({ mode, model, onClose, onSaved }) {
  const [form, setForm] = useState({
    service: model?.service || '',
    account_username: model?.account_username || '',
    url: model?.url || '',
    description: model?.description || '',
    password: '',
  });
  const [showPwd, setShowPwd] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === 'create') {
        await api.post('/api/passwords', form);
      } else {
        const payload = { ...form };
        if (!payload.password) delete payload.password;
        await api.put(`/api/passwords/${model.id}`, payload);
      }
      onSaved();
    } catch (e) {
      setError(e.response?.data?.detail || 'Salvataggio fallito');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={overlayStyle} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={modalStyle}>
        <h2 style={{ marginTop: 0 }}>{mode === 'create' ? 'Nuova password' : 'Modifica password'}</h2>
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label>Servizio *</label>
            <input value={form.service} onChange={e => setForm({ ...form, service: e.target.value })} required placeholder="es. Gmail, AWS console" />
          </div>
          <div className="form-group">
            <label>Utente *</label>
            <input value={form.account_username} onChange={e => setForm({ ...form, account_username: e.target.value })} required placeholder="es. mario@gmail.com" />
          </div>
          <div className="form-group">
            <label>Password {mode === 'edit' ? '(lasciare vuoto per non modificare)' : '*'}</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                type={showPwd ? 'text' : 'password'}
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                required={mode === 'create'}
                autoComplete="new-password"
                style={{ flex: 1 }}
              />
              <button type="button" className="btn-secondary" onClick={() => setShowPwd(!showPwd)}>
                {showPwd ? 'Nascondi' : 'Mostra'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => { setForm({ ...form, password: generatePassword() }); setShowPwd(true); }}>
                Genera
              </button>
            </div>
          </div>
          <div className="form-group">
            <label>URL</label>
            <input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })} placeholder="https://" />
          </div>
          <div className="form-group">
            <label>Descrizione</label>
            <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} placeholder="es. account amministratore di produzione" />
          </div>
          {error && <p className="error">{error}</p>}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
            <button type="button" className="btn-secondary" onClick={onClose}>Annulla</button>
            <button type="submit" className="btn-primary" disabled={busy}>
              {busy ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
