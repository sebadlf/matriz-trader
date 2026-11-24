import type { ThemeConfig } from "antd";

// Tema de Ant Design. Los defaults de AntD no alcanzan el contraste 4.5:1 de WCAG 1.4.3
// sobre el fondo del Layout (#f5f5f5): `e2e/a11y.spec.ts` (axe) lo verifica.
export const theme: ThemeConfig = {
  token: {
    // blue-7 de la paleta de AntD: 5.6:1 sobre #f5f5f5 (el blue-6 por defecto da 3.8:1).
    colorPrimary: "#0958d9",
    colorLink: "#0958d9",
    // Texto descriptivo (p. ej. subtítulos de `Result`): 65 % de opacidad en lugar de 45 %.
    colorTextDescription: "rgba(0, 0, 0, 0.65)",
    // Placeholder de `Select`/`Input`: 55 % (#737373, 4.7:1 sobre blanco) en lugar de 25 % (1.8:1).
    colorTextPlaceholder: "rgba(0, 0, 0, 0.55)",
  },
};
