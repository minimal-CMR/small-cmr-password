import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import UnlockDialog from '../UnlockDialog.vue';

describe('UnlockDialog.vue', () => {
  it('renders title + description from props', () => {
    const w = mount(UnlockDialog, {
      props: { title: 'Sblocca', description: 'Inserisci pwd', submitLabel: 'OK' },
      attachTo: document.body,
    });
    expect(document.body.textContent).toContain('Sblocca');
    expect(document.body.textContent).toContain('Inserisci pwd');
    w.unmount();
  });

  it('shows error prop', () => {
    const w = mount(UnlockDialog, {
      props: { error: 'Password errata' },
      attachTo: document.body,
    });
    expect(document.body.textContent).toContain('Password errata');
    w.unmount();
  });

  it('emits cancel when annulla clicked', async () => {
    const w = mount(UnlockDialog, { attachTo: document.body });
    const buttons = document.body.querySelectorAll('button');
    const cancel = [...buttons].find(b => b.textContent.trim() === 'Annulla');
    cancel.click();
    await new Promise(r => setTimeout(r, 0));
    expect(w.emitted('cancel')).toBeTruthy();
    w.unmount();
  });

  it('emits confirmed with pwd on submit', async () => {
    const w = mount(UnlockDialog, { props: { submitLabel: 'Sblocca' }, attachTo: document.body });
    const input = document.body.querySelector('input[type="password"]');
    input.value = 'mypwd';
    input.dispatchEvent(new Event('input'));
    await new Promise(r => setTimeout(r, 0));

    const buttons = document.body.querySelectorAll('button');
    const submit = [...buttons].find(b => b.textContent.trim().includes('Sblocca') || b.textContent.trim().includes('Verifica'));
    submit.click();
    await new Promise(r => setTimeout(r, 0));

    expect(w.emitted('confirmed')).toBeTruthy();
    expect(w.emitted('confirmed')[0][0]).toBe('mypwd');
    w.unmount();
  });
});
