// Probe de verify-guards: ciclo _probeB → _probeA → _probeB (AC-30, no-circular).
import { a } from "@/utils/_probeA";

export const b = (): number => a() - 1;
