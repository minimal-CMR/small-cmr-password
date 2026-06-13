import React, { useEffect, useState } from 'react';
import api from '../api/client';

const overlayStyle = {
  position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
  display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16,
};

const modalStyle = {
  background: '#fff', borderRadius: 8, padding: 20,
  width: '100%', maxWidth: 640, maxHeight: '90vh',
  display: 'flex', flexDirection: 'column',
  boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
};

export default function ShareDialog({ password, me, onClose, onUpdated }) {
  const [users, setUsers] = useState([]);
  const [ditte, setDitte] = useState([]);
  const [teams, setTeams] = useState([]);
  const [perms, setPerms] = useState(new Map()); // userId -> 'read'|'write'
  const [original, setOriginal] = useState(new Set());

  const [fNome, setFNome] = useState('');
  const [fCognome, setFCognome] = useState('');
  const [fDitta, setFDitta] = useState('');
  const [fTeam, setFTeam] = useState('');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [u, d, t, shares] = await Promise.all([
          api.get('/api/users'),
          api.get('/api/ditte').catch(() => ({ data: [] })),
          api.get('/api/teams').catch(() => ({ data: [] })),
          api.get(`/api/passwords/${password.id}/shares`),
        ]);
        setUsers(u.data.filter(x => x.id !== me?.id && x.id !== password.owner.id));
        setDitte(d.data);
        setTeams(t.data);
        const sharedMap = new Map();
        const sharedIds = new Set();
        shares.data.forEach(s => {
          sharedMap.set(s.recipient.id, s.permission);
          sharedIds.add(s.recipient.id);
        });
        setPerms(sharedMap);
        setOriginal(sharedIds);
      } catch (e) {
        setError(e.response?.data?.detail || 'Errore caricamento');
      }
    })();
  }, [password.id, me?.id]);

  const teamMemberIds = fTeam ? new Set((teams.find(t => t.id === Number(fTeam))?.members || []).map(m => m.id)) : null;

  const visibleUsers = users.filter(u => {
    if (fNome.trim() && !(u.nome || '').toLowerCase().includes(fNome.trim().toLowerCase())) return false;
    if (fCognome.trim() && !(u.cognome || '').toLowerCase().includes(fCognome.trim().toLowerCase())) return false;
    if (fDitta && u.ditta_id !== Number(fDitta)) return false;
    if (teamMemberIds && !teamMemberIds.has(u.id)) return false;
    return true;
  });

  const toggleUser = (uid) => {
    const next = new Map(perms);
    if (next.has(uid)) next.delete(uid);
    else next.set(uid, 'read');
    setPerms(next);
  };

  const setPermission = (uid, perm) => {
    const next = new Map(perms);
    next.set(uid, perm);
    setPerms(next);
  };

  const selectAll = () => {
    const next = new Map(perms);
    visibleUsers.forEach(u => { if (!next.has(u.id)) next.set(u.id, 'read'); });
    setPerms(next);
  };

  const deselectAll = () => {
    const next = new Map(perms);
    visibleUsers.forEach(u => next.delete(u.id));
    setPerms(next);
  };

  const shareWithTeam = async () => {
    if (!fTeam) return;
    if (!window.confirm('Condividere con tutti i membri del team selezionato?')) return;
    try {
      await api.post(`/api/passwords/${password.id}/shares/team/${fTeam}?permission=read`);
      onUpdated();
      onClose();
    } catch (e) {
      setError(e.response?.data?.detail || 'Condivisione team fallita');
    }
  };

  const shareWithDitta = async () => {
    if (!fDitta) return;
    if (!window.confirm('Condividere con tutti gli utenti della ditta selezionata?')) return;
    try {
      await api.post(`/api/passwords/${password.id}/shares/ditta/${fDitta}?permission=read`);
      onUpdated();
      onClose();
    } catch (e) {
      setError(e.response?.data?.detail || 'Condivisione ditta fallita');
    }
  };

  const onSave = async () => {
    setBusy(true);
    setError(null);
    try {
      const recipients = Array.from(perms.entries()).map(([user_id, permission]) => ({ user_id, permission }));
      if (recipients.length) {
        await api.post(`/api/passwords/${password.id}/shares`, { recipients });
      }
      const toRevoke = [...original].filter(id => !perms.has(id));
      await Promise.all(toRevoke.map(id => api.delete(`/api/passwords/${password.id}/shares/${id}`)));
      onUpdated();
      onClose();
    } catch (e) {
      setError(e.response?.data?.detail || 'Errore di condivisione');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={overlayStyle} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={modalStyle}>
        <h2 style={{ marginTop: 0, marginBottom: 4 }}>Condividi password</h2>
        <p style={{ color: '#666', marginBottom: 16 }}>{password.service} — {password.account_username}</p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 8, marginBottom: 12 }}>
          <div className="form-group">
            <label>Nome</label>
            <input value={fNome} onChange={e => setFNome(e.target.value)} placeholder="es. Mario" />
          </div>
          <div className="form-group">
            <label>Cognome</label>
            <input value={fCognome} onChange={e => setFCognome(e.target.value)} placeholder="es. Rossi" />
          </div>
          <div className="form-group">
            <label>Ditta</label>
            <select value={fDitta} onChange={e => setFDitta(e.target.value)}>
              <option value="">Tutte</option>
              {ditte.map(d => <option key={d.id} value={d.id}>{d.nome}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Team</label>
            <select value={fTeam} onChange={e => setFTeam(e.target.value)}>
              <option value="">Tutti</option>
              {teams.map(t => <option key={t.id} value={t.id}>{t.name} ({(t.members || []).length})</option>)}
            </select>
          </div>
        </div>

        {(fDitta || fTeam) && (
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            {fTeam && <button className="btn-secondary btn-sm" onClick={shareWithTeam}>Condividi con team intero</button>}
            {fDitta && <button className="btn-secondary btn-sm" onClick={shareWithDitta}>Condividi con ditta intera</button>}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, fontSize: '0.9em' }}>
          <span>
            <strong>Utenti</strong>
            <span style={{ color: '#999', marginLeft: 6 }}>({perms.size} selezionati di {visibleUsers.length})</span>
          </span>
          <div style={{ display: 'flex', gap: 12 }}>
            <button className="link-btn" onClick={selectAll}>Tutti</button>
            <button className="link-btn" onClick={deselectAll}>Nessuno</button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #ddd', borderRadius: 6, marginBottom: 16, minHeight: 160, maxHeight: 280 }}>
          {visibleUsers.length === 0 ? (
            <div style={{ padding: 16, textAlign: 'center', color: '#999', fontSize: '0.9em' }}>Nessun utente trovato</div>
          ) : visibleUsers.map(u => {
            const selected = perms.has(u.id);
            const perm = perms.get(u.id);
            return (
              <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 12px', borderBottom: '1px solid #f0f0f0' }}>
                <input type="checkbox" checked={selected} onChange={() => toggleUser(u.id)} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.9em', fontWeight: 500 }}>{u.nome} {u.cognome}</div>
                  <div style={{ fontSize: '0.78em', color: '#999' }}>{u.email}</div>
                </div>
                {selected ? (
                  <div style={{ display: 'flex', borderRadius: 4, overflow: 'hidden', border: '1px solid #ddd' }}>
                    <button onClick={() => setPermission(u.id, 'read')}
                            style={{ padding: '2px 8px', fontSize: '0.75em', border: 'none',
                                     background: perm === 'read' ? '#3b82f6' : '#fff',
                                     color: perm === 'read' ? '#fff' : '#666', cursor: 'pointer' }}>
                      Vista
                    </button>
                    <button onClick={() => setPermission(u.id, 'write')}
                            style={{ padding: '2px 8px', fontSize: '0.75em', border: 'none', borderLeft: '1px solid #ddd',
                                     background: perm === 'write' ? '#f59e0b' : '#fff',
                                     color: perm === 'write' ? '#fff' : '#666', cursor: 'pointer' }}>
                      Modifica
                    </button>
                  </div>
                ) : (
                  <span style={{ color: '#ccc', fontSize: '0.75em', width: 90, textAlign: 'right' }}>—</span>
                )}
              </div>
            );
          })}
        </div>

        {error && <p className="error">{error}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn-secondary" onClick={onClose}>Chiudi</button>
          <button className="btn-primary" onClick={onSave} disabled={busy}>
            {busy ? 'Salvataggio...' : 'Salva'}
          </button>
        </div>
      </div>
    </div>
  );
}
