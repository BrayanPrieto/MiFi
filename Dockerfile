# Build stage
FROM node:22-alpine as build-stage

WORKDIR /app

# Habilitar pnpm vía corepack (incluido en Node)
RUN corepack enable

# Copiar archivos de dependencias (incluye pnpm-workspace.yaml con la config de builds)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Instalar dependencias (lockfile inmutable para builds reproducibles)
RUN pnpm install --frozen-lockfile

# Copiar el resto del código del frontend
COPY . .

# Construir la aplicación web estática
RUN pnpm build

# Production stage (Servir con Nginx + HTTPS)
FROM nginx:stable-alpine as production-stage

# Instalar openssl para generar cert autofirmado
RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/self-signed.key \
    -out /etc/nginx/ssl/self-signed.crt \
    -subj '/CN=localhost' -batch

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puertos HTTP + HTTPS
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
