// Probe de verify-guards: un hook compartido importa de components/ (AC-30, hooks-limites).
import { ProbeComp } from "@/components/_probeComp";

export const useProbe = (): typeof ProbeComp => ProbeComp;
