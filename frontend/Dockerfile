# syntax=docker/dockerfile:1.7
#
# Targets:
#   dev   -> Node + pnpm + dependencias completas; `vp dev` con HMR (código montado por compose)
#   build -> instala con el lockfile congelado y genera dist/ con `vp build`
#   prod  -> nginx sin privilegios que sirve dist/ en :8080 y hace proxy de /api al backend.
#            No contiene Node ni dependencias de desarrollo (AC-30).
#
#   docker build --target prod -t matriz-trader-frontend frontend

FROM node:22-slim AS deps
ENV PNPM_HOME=/pnpm \
    PATH=/app/node_modules/.bin:/pnpm:$PATH \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    pnpm config set store-dir /pnpm/store && pnpm install --frozen-lockfile

FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["vp", "dev", "--host", "0.0.0.0", "--port", "5173"]

FROM deps AS build
COPY . .
RUN vp build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
