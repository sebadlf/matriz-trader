import { setupServer } from "msw/node";

/**
 * Servidor MSW compartido por todos los tests unitarios. Arranca sin handlers:
 * cada test registra los suyos con `server.use(...)` (p. ej. los generados por Orval en `*.msw.ts`).
 */
export const server = setupServer();
