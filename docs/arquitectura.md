# Arquitectura MiFi

MiFi está diseñado como un Monorepo con separación estricta de responsabilidades (Frontend local y Backend remoto/localizado).

## 1. Frontend: Cliente "Thin" Nativo
Construido usando **Tauri v2** + **Vue 3** + **TailwindCSS** + **PrimeVue**.
- Tauri permite compilar una app nativa hiper-ligera apoyándose en el WebView OS Nativo.
- Usamos **Pinia** para mantener la Single Source of Truth del estado (Tokens, Perfil, Caching local).
- Las llamadas de red pasan por un interceptor global de **Axios**.

## 2. Backend: Motor "Thick" de Negocio
Construido con **Python (FastAPI)** + **PostgreSQL** (Neon/Supabase en Producción).
Todo lo relacionado con dinero, cálculo de saldos y autenticación no pasa en la App, pasa en la BDD.
- **Seguridad**: Hash BCrypt, JWT Tokens.
- **Persistencia**: SQLAlchemy ORM + Alembic Migraciones.
- **Triggers BBDD**: Toda transacción actualiza automáticamente (`AFTER INSERT OR UPDATE`) el nivel de la cuenta padre en POSTGRES, evitando desfasajes de la interfaz.

## 3. Integración de IA Local
El motor RAG (Ollama) funciona como un controlador separado del backend, ejecutado preferiblemente en local o un server edge, transformando un Input Humano (*Text*) a una Estructura Parseable (*JSON Schema* de `TransaccionCreate`).
