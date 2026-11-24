// Probe de verify-guards: `fetch` y `window.fetch` fuera de src/api/mutator.ts (AC-27).
export const cargar = async (): Promise<unknown> => {
  const respuesta = await fetch("/api/health");
  const otra = await window.fetch("/api/health");
  return [await respuesta.json(), await otra.json()];
};
