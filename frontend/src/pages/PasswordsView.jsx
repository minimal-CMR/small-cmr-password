import React, { useEffect, useState } from 'react';
import api from '../api/client';
import PasswordDialog from '../components/PasswordDialog';
import ShareDialog from '../components/ShareDialog';
import RevealDialog from '../components/RevealDialog';
import ConfirmPasswordDialog from '../components/ConfirmPasswordDialog';

const defaultSearch = () => ({
  account_username: '',
  service: '',
  description: '',
  owner_email: '',
  include_shared: true,
});

export default function PasswordsView() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState(defaultSearch());

  const [dialog, setDialog] = useState({ open: false, mode: 'create', model: null });
  const [shareDlg, setShareDlg] = useState({ open: false, password: null });
  const [confirmDlg, setConfirmDlg] = useState({ open: false, item: null, mode: 'reveal' });
  const [revealDlg, setRevealDlg] = useState({ open: false, item: null });

  const [me, setMe] = useState(null);

  useEffect(() => {
    api.get('/api/auth/me').then(r => setMe(r.data)).catch(() => setMe(null));
  }, []);

  const isAdmin = me?.ruoli?.includes('admin');

  const loadList = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      Object.entries(search).forEach(([k, v]) => {
        if (v === '' || v === null || v === undefined) return;
        params[k] = v;
      });
      const { data } = await api.get('/api/passwords', { params });
      setItems(data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Errore caricamento');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadList(); }, []);

  const canEdit = (p) => isAdmin || p.owner?.id === me?.id || p.my_permission === 'write';
  const canShare = canEdit;

  const openCreate = () => setDialog({
    open: true, mode: 'create',
    model: { account_username: '', service: '', description: '', url: '', password: '' },
  });

  const openEdit = (p) => setDialog({
    open: true, mode: 'edit',
    model: { ...p, password: '' },
  });

  const onDelete = async (p) => {
    if (!window.confirm(`Eliminare la password per "${p.service}" (${p.account_username})?`)) return;
    try {
      await api.delete(`/api/passwords/${p.id}`);
      loadList();
    } catch (e) {
      alert(e.response?.data?.detail || 'Eliminazione fallita');
    }
  };

  const askThenReveal = (p) => setConfirmDlg({ open: true, item: p, mode: 'reveal' });
  const askThenCopy = (p) => setConfirmDlg({ open: true, item: p, mode: 'copy' });

  const onPasswordConfirmed = async (userPassword) => {
    const { item, mode } = confirmDlg;
    setConfirmDlg({ open: false, item: null, mode: 'reveal' });
    try {
      const { data } = await api.post(`/api/passwords/${item.id}/reveal`, { user_password: userPassword });
      if (mode === 'copy') {
        await navigator.clipboard.writeText(data.password);
        alert('Password copiata negli appunti');
      } else {
        setRevealDlg({ open: true, item: { service: item.service, account: item.account_username, password: data.password } });
      }
    } catch (e) {
      alert(e.response?.data?.detail || 'Password vault errata o accesso non consentito');
    }
  };

  const onSaved = () => {
    setDialog({ open: false, mode: 'create', model: null });
    loadList();
  };

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1>Le mie password</h1>
        <button className="btn-primary" onClick={openCreate}>+ Nuova password</button>
      </div>

      <div className="card" style={{ padding: 16, marginBottom: 20 }}>
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: '1rem' }}>Ricerca</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          <div className="form-group">
            <label>Utente</label>
            <input value={search.account_username}
                   onChange={e => setSearch({ ...search, account_username: e.target.value })}
                   placeholder="es. mario@gmail.com" />
          </div>
          <div className="form-group">
            <label>Servizio</label>
            <input value={search.service}
                   onChange={e => setSearch({ ...search, service: e.target.value })}
                   placeholder="es. AWS, Gmail" />
          </div>
          <div className="form-group">
            <label>Descrizione</label>
            <input value={search.description}
                   onChange={e => setSearch({ ...search, description: e.target.value })}
                   placeholder="es. produzione" />
          </div>
          {isAdmin && (
            <div className="form-group">
              <label>Email proprietario</label>
              <input value={search.owner_email}
                     onChange={e => setSearch({ ...search, owner_email: e.target.value })}
                     placeholder="es. luca@azienda.com" />
            </div>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, flexWrap: 'wrap', gap: 8 }}>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" checked={search.include_shared}
                   onChange={e => setSearch({ ...search, include_shared: e.target.checked })} />
            <span>Includi password condivise con me</span>
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-secondary" onClick={() => { setSearch(defaultSearch()); setTimeout(loadList, 0); }}>Reset</button>
            <button className="btn-primary" onClick={loadList}>Cerca</button>
          </div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#666' }}>Caricamento...</div>
        ) : error ? (
          <div className="error" style={{ padding: 16 }}>{error}</div>
        ) : items.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#666' }}>
            Nessuna password trovata. Crea la prima cliccando su "+ Nuova password".
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Servizio</th>
                <th>Utente</th>
                <th>Descrizione</th>
                <th>Proprietario</th>
                <th style={{ textAlign: 'right' }}>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {items.map(p => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.service}</strong>
                    {p.shared && <span className="badge" style={{ marginLeft: 6 }}>condivisa</span>}
                  </td>
                  <td>{p.account_username}</td>
                  <td style={{ color: '#666' }}>{p.description}</td>
                  <td>
                    <div>{p.owner?.nome} {p.owner?.cognome}</div>
                    <div style={{ fontSize: '0.85em', color: '#999' }}>{p.owner?.email}</div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 4, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      <button className="btn-secondary btn-sm" onClick={() => askThenCopy(p)}>Copia</button>
                      <button className="btn-secondary btn-sm" onClick={() => askThenReveal(p)}>Mostra</button>
                      {canShare(p) && <button className="btn-secondary btn-sm" onClick={() => setShareDlg({ open: true, password: p })}>Condividi</button>}
                      {canEdit(p) && <button className="btn-secondary btn-sm" onClick={() => openEdit(p)}>Modifica</button>}
                      {canEdit(p) && <button className="btn-secondary btn-sm" style={{ color: '#c00' }} onClick={() => onDelete(p)}>Elimina</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {dialog.open && (
        <PasswordDialog
          mode={dialog.mode}
          model={dialog.model}
          onClose={() => setDialog({ ...dialog, open: false })}
          onSaved={onSaved}
        />
      )}

      {shareDlg.open && (
        <ShareDialog
          password={shareDlg.password}
          me={me}
          onClose={() => setShareDlg({ open: false, password: null })}
          onUpdated={loadList}
        />
      )}

      {confirmDlg.open && (
        <ConfirmPasswordDialog
          onConfirmed={onPasswordConfirmed}
          onCancel={() => setConfirmDlg({ open: false, item: null, mode: 'reveal' })}
        />
      )}

      {revealDlg.open && (
        <RevealDialog
          item={revealDlg.item}
          onClose={() => setRevealDlg({ open: false, item: null })}
        />
      )}
    </div>
  );
}
