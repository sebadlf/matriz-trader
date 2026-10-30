# Imagen de producción del frontend (AC-30, AC-31, AC-40). Contexto de build: raíz del repo.
FROM node:24-alpine AS build

WORKDIR /app/frontend

# Dependencias primero (capa cacheable).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# `prebuild` genera el cliente de Orval desde `openapi.json`; en producción la API va por nginx.
COPY frontend/ ./
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80
