import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { h } from 'vue';
import { NMessageProvider } from 'naive-ui';
import PasswordDialog from '../PasswordDialog.vue';
import api from '../../api/client';

vi.mock('../../api/client', () => ({
  default: { post: vi.fn(), put: vi.fn() },
}));

function wrap(props) {
  // PasswordDialog usa useMessage() → richiede NMessageProvider
  return mount({
    render: () => h(NMessageProvider, null, () => h(PasswordDialog, props)),
  }, { attachTo: document.body });
}

describe('PasswordDialog.vue', () => {
  beforeEach(() => vi.clearAllMocks());

  it('title differs by mode (create vs edit)', () => {
    const c = wrap({ mode: 'create', model: {} });
    expect(document.body.textContent).toContain('Nuova password');
    c.unmount();
    const e = wrap({ mode: 'edit', model: { id: 1, service: 'X', account_username: 'a' } });
    expect(document.body.textContent).toContain('Modifica password');
    e.unmount();
  });

  it('"Genera" button fills the password field with a random string', async () => {
    const w = wrap({ mode: 'create', model: {} });
    const buttons = document.body.querySelectorAll('button');
    const gen = [...buttons].find(b => b.textContent.trim() === 'Genera');
    gen.click();
    await new Promise(r => setTimeout(r, 0));
    const pwInput = document.body.querySelector('input[placeholder="••••••••"]');
    expect(pwInput.value.length).toBeGreaterThanOrEqual(20);
    w.unmount();
  });

  it('create posts to /api/passwords on save', async () => {
    api.post.mockResolvedValueOnce({ data: { id: 99 } });
    const w = wrap({ mode: 'create', model: {} });

    // Compila i tre campi richiesti
    const inputs = document.body.querySelectorAll('input');
    const setVal = (el, val) => {
      el.value = val; el.dispatchEvent(new Event('input'));
    };
    setVal(inputs[0], 'Gmail');      // service
    setVal(inputs[1], 'me@x.it');    // account
    setVal(inputs[2], 'secret123');  // password (visible)
    await new Promise(r => setTimeout(r, 0));

    const saveBtn = [...document.body.querySelectorAll('button')]
      .find(b => b.textContent.trim() === 'Salva');
    saveBtn.click();
    await new Promise(r => setTimeout(r, 50));

    expect(api.post).toHaveBeenCalledWith('/api/passwords', expect.objectContaining({
      service: 'Gmail',
      account_username: 'me@x.it',
      password: 'secret123',
    }));
    w.unmount();
  });
});
