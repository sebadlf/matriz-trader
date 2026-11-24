// Probe de verify-guards: un componente compartido importa de api/ (AC-30, components-limites).
import { createQueryClient } from "@/api/queryClient";

export const cliente = createQueryClient();
