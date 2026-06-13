import React, { useEffect, useRef, useState } from 'react';

const overlayStyle = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110, padding: 16,
};

const modalStyle = {
  background: '#fff', borderRadius: 8, padding: 24,
  width: '100%', maxWidth: 380, boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
};

export default function ConfirmPasswordDialog({ onConfirmed, onCancel }) {
  const [pwd, setPwd] = useState('');
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      onConfirmed(pwd);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={overlayStyle} onClick={e => e.target === e.currentTarget && onCancel()}>
      <div style={modalStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Conferma identità</h2>
        <p style={{ color: '#666', fontSize: '0.9em', marginBottom: 16 }}>
          Inserisci la tua password per visualizzare la password salvata.
        </p>
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label>La tua password</label>
            <input
              ref={inputRef}
              type="password"
              value={pwd}
              onChange={e => setPwd(e.target.value)}
              required
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
            <button type="button" className="btn-secondary" onClick={onCancel}>Annulla</button>
            <button type="submit" className="btn-primary" disabled={busy || !pwd}>
              {busy ? 'Verifica...' : 'Conferma'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
