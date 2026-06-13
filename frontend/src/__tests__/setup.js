import { vi, beforeEach } from 'vitest';

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

// Mock clipboard (RevealDialog usa navigator.clipboard.writeText)
if (!navigator.clipboard) {
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: vi.fn(() => Promise.resolve()) },
    writable: true,
  });
}
