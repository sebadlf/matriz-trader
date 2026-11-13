// Clasificación única de estados de orden (EB-6): la usan el refresco periódico y la cancelabilidad.

export const FINAL_STATUSES = ['REJECTED', 'CANCELLED', 'REPLACED', 'FILLED'] as const;

export const NON_FINAL_STATUSES = [
  'NEW',
  'PENDING_NEW',
  'PENDING_REPLACE',
  'PENDING_CANCEL',
  'PENDING_APPROVAL',
  'PARTIALLY_FILLED',
] as const;

const FINAL_SET: ReadonlySet<string> = new Set(FINAL_STATUSES);

/** `null`, `undefined` o un valor fuera del enum se tratan como no finales. */
export function isFinalStatus(status: string | null | undefined): boolean {
  return status != null && FINAL_SET.has(status);
}

/** Cancelable si no es final y no está ya en `PENDING_CANCEL` (EB-11, EB-12). */
export function isCancelable(status: string | null | undefined): boolean {
  return !isFinalStatus(status) && status !== 'PENDING_CANCEL';
}

/** `true` si al menos un estado es no final: el listado debe seguir refrescándose (EB-7, EB-8). */
export function hasNonFinal(statuses: readonly (string | null | undefined)[]): boolean {
  return statuses.some((status) => !isFinalStatus(status));
}

/** Estado a mostrar: `PENDING_CANCEL` tras una cancelación aceptada mientras la API no informe un final (EB-15). */
export function effectiveStatus(
  apiStatus: string | null | undefined,
  pendingCancel: boolean,
): string | null | undefined {
  return pendingCancel && !isFinalStatus(apiStatus) ? 'PENDING_CANCEL' : apiStatus;
}
