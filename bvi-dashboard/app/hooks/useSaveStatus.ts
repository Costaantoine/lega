'use client';
import { useState } from 'react';

type Status = 'idle' | 'saving' | 'success' | 'error';

export function useSaveStatus() {
  const [status, setStatus] = useState<Status>('idle');

  const save = async (fn: () => Promise<any>) => {
    setStatus('saving');
    try {
      await fn();
      setStatus('success');
      setTimeout(() => setStatus('idle'), 2500);
    } catch {
      setStatus('error');
      setTimeout(() => setStatus('idle'), 3000);
    }
  };

  const buttonStyle = (base: React.CSSProperties = {}): React.CSSProperties => ({
    ...base,
    background:
      status === 'success' ? '#166534' :
      status === 'error'   ? '#7f1d1d' :
      status === 'saving'  ? '#334155' :
      (base.background as string) || '#3b82f6',
    cursor: status === 'saving' ? 'not-allowed' : 'pointer',
    opacity: status === 'saving' ? 0.7 : 1,
    transition: 'background 300ms ease',
  });

  const buttonLabel = (base: string) =>
    status === 'saving' ? '⏳ Sauvegarde...' :
    status === 'success' ? '✅ Sauvegardé' :
    status === 'error'   ? '✗ Erreur' : base;

  return { status, save, buttonStyle, buttonLabel };
}
