// Reglas de dependencia entre carpetas de src/ (frontend/CLAUDE.md §3). Se verifican sobre rutas resueltas,
// incluido el alias @/ (vía tsconfig.json). Lo ejecuta `vp run lint:arch` (AC-29, AC-30).
/** @type {import("dependency-cruiser").IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      comment: "Prohibidas las dependencias circulares.",
      severity: "error",
      from: {},
      to: { circular: true },
    },
    {
      name: "screen-no-otra-screen",
      comment: "Una pantalla nunca importa de otra pantalla: subí lo común a components/ o hooks/.",
      severity: "error",
      from: { path: "^src/screens/([^/]+)/" },
      to: { path: "^src/screens/", pathNot: "^src/screens/$1/" },
    },
    {
      name: "components-limites",
      comment: "components/ solo importa de hooks, utils, constants y types.",
      severity: "error",
      from: { path: "^src/components/" },
      to: { path: "^src/(screens|api|stores|layouts)/" },
    },
    {
      name: "hooks-limites",
      comment: "hooks/ no importa de screens, components ni layouts.",
      severity: "error",
      from: { path: "^src/hooks/" },
      to: { path: "^src/(screens|components|layouts)/" },
    },
    {
      name: "utils-constants-puros",
      comment:
        "utils/ y constants/ solo importan de types/ (y entre sí); sin React ni paquetes npm.",
      severity: "error",
      // Los tests de utils/ importan el runner (vite-plus/test): no son código de la capa.
      from: { path: "^src/(utils|constants)/", pathNot: "\\.test\\.tsx?$" },
      // Sin filtro por `dependencyTypes`: con el parser swc los imports con @/ quedan como
      // "undetermined" y el filtro los dejaba pasar. Todo destino fuera de types/utils/constants
      // (incluidos los paquetes npm, resueltos a node_modules/) es una violación.
      to: { pathNot: "^src/(types|utils|constants)/" },
    },
    {
      name: "screen-via-index",
      comment: "Fuera de su pantalla (y de app/), se importa solo el index.ts de cada pantalla.",
      severity: "error",
      from: { pathNot: "^src/(screens|app)/" },
      to: { path: "^src/screens/[^/]+/(?!index\\.ts$)" },
    },
  ],
  options: {
    // TypeScript 7 no expone la API que usa dependency-cruiser: el parseo de TS/TSX lo hace swc.
    parser: "swc",
    tsConfig: { fileName: "tsconfig.json" },
    doNotFollow: { path: "node_modules" },
    exclude: { path: "^src/api/generated/" },
  },
};
