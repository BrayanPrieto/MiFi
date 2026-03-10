# Build stage
FROM node:20-alpine as build-stage

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código del frontend
COPY . .

# Construir la aplicación web estática
RUN npm run build

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
