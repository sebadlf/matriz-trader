import { describe, expect, it } from 'vitest';
import { effectiveStatus, hasNonFinal, isCancelable, isFinalStatus } from './orderStatus';

describe('clasificación de estados (EB-6)', () => {
  it.each([
    ['NEW', false, true],
    ['PENDING_NEW', false, true],
    ['PENDING_REPLACE', false, true],
    ['PENDING_CANCEL', false, false],
    ['PENDING_APPROVAL', false, true],
    ['PARTIALLY_FILLED', false, true],
    ['REJECTED', true, false],
    ['CANCELLED', true, false],
    ['REPLACED', true, false],
    ['FILLED', true, false],
    [null, false, true],
    [undefined, false, true],
    ['FOO', false, true],
  ] as const)('%s → final=%s, cancelable=%s', (status, final, cancelable) => {
    expect(isFinalStatus(status)).toBe(final);
    expect(isCancelable(status)).toBe(cancelable);
  });
});

describe('hasNonFinal', () => {
  it('es false con lista vacía o todo final', () => {
    expect(hasNonFinal([])).toBe(false);
    expect(hasNonFinal(['FILLED', 'CANCELLED', 'REJECTED', 'REPLACED'])).toBe(false);
  });

  it('es true si hay al menos un no final, nulo o desconocido', () => {
    expect(hasNonFinal(['FILLED', 'NEW'])).toBe(true);
    expect(hasNonFinal(['FILLED', null])).toBe(true);
    expect(hasNonFinal(['FILLED', 'FOO'])).toBe(true);
  });
});

describe('effectiveStatus', () => {
  it('sin cancelación pendiente devuelve el estado de la API', () => {
    expect(effectiveStatus('NEW', false)).toBe('NEW');
    expect(effectiveStatus(null, false)).toBeNull();
  });

  it('con cancelación pendiente muestra PENDING_CANCEL mientras no sea final', () => {
    expect(effectiveStatus('NEW', true)).toBe('PENDING_CANCEL');
    expect(effectiveStatus(null, true)).toBe('PENDING_CANCEL');
    expect(effectiveStatus('CANCELLED', true)).toBe('CANCELLED');
    expect(effectiveStatus('FILLED', true)).toBe('FILLED');
  });
});
