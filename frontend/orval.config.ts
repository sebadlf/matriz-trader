import { defineConfig } from 'orval';

// Genera los hooks de react-query desde el esquema versionado del backend (AC-6).
export default defineConfig({
  matriz: {
    input: { target: './openapi.json' },
    output: {
      target: 'src/api/generated/matriz.ts',
      schemas: 'src/api/generated/model',
      client: 'react-query',
      httpClient: 'fetch',
      clean: true,
      override: { mutator: { path: './src/api/http.ts', name: 'customFetch' } },
    },
  },
});
