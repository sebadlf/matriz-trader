// Probe de verify-guards: ciclo _probeA → _probeB → _probeA (AC-30, no-circular).
import { b } from "@/utils/_probeB";

export const a = (): number => b() + 1;
