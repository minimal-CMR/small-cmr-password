import React, { useEffect, useState } from 'react';

const overlayStyle = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16,
};

const modalStyle = {
  background: '#fff', borderRadius: 8, padding: 24,
  width: '100%', maxWidth: 440, boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
};

export default function RevealDialog({ item, onClose }) {
  const [show, setShow] = useState(false);
  const [countdown, setCountdown] = useState(30);

  useEffect(() => {
    const id = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { onClose(); return 0; }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [onClose]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(item.password);
      alert('Password copiata');
    } catch {
      alert('Copia fallita');
    }
  };

  return (
    <div style={overlayStyle} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={modalStyle}>
        <h2 style={{ marginTop: 0, marginBottom: 4 }}>{item.service}</h2>
        <p style={{ color: '#666', marginBottom: 16 }}>{item.account}</p>

        <div className="form-group">
          <label>Password</label>
          <div style={{ display: 'flex', gap: 6 }}>
            <input value={item.password} readOnly type={show ? 'text' : 'password'} style={{ flex: 1, fontFamily: 'monospace' }} />
            <button className="btn-secondary" onClick={() => setShow(!show)}>{show ? 'Nascondi' : 'Mostra'}</button>
            <button className="btn-primary" onClick={copy}>Copia</button>
          </div>
        </div>

        <p style={{ fontSize: '0.85em', color: '#999' }}>Chiusura automatica tra {countdown}s</p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
          <button className="btn-secondary" onClick={onClose}>Chiudi</button>
        </div>
      </div>
    </div>
  );
}
