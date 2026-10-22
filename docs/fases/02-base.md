# Fase 02 — Base, diseño y autenticación

## Implementado

- Frontend Vue 3 + TypeScript + Tailwind 4, Vite, Router y Pinia.
- Diseño HassLab: menú lateral, navegación responsiva, estados vacíos, avisos y login.
- Django 5.2 + DRF, usuario personalizado, JWT con rotación/blacklist de refresh.
- Roles administrador/investigador, perfil y creación de cuentas por administrador.
- PostgreSQL como configuración normal; SQLite únicamente para pruebas aisladas.
- Archivos privados servidos por API autenticada. Variables de entorno sin credenciales reales en Git.
- Migraciones y pipeline CI con PostgreSQL 17 y build frontend.

## Comprobaciones reales

- 4 pruebas de autenticación aprobadas: login/refresh/logout, usuario inactivo, creación de usuario/contraseña y prevención de escalamiento de rol.
- `npm run build`: TypeScript y Vite completados, 1687 módulos transformados.
- `manage.py check --settings=config.test_settings`: sin errores.
- GitHub Actions run 39619785356: backend y frontend completados con éxito. PostgreSQL 17: migraciones, check y suite aprobados. La prueba visual de login, navegación y ancho móvil también pasó en el run 39708069205.

## Cómo probar

Consultar README (en preparación) para crear `.env`, PostgreSQL y usuario administrador. Ejecutar Django y Vite en terminales separadas. No hay contraseña predeterminada.

## Decisiones

Los tokens se conservan en memoria; recargar requiere login. El investigador no puede autoconcederse rol administrador. La documentación OpenAPI está en `/api/v1/schema/` y `/api/v1/docs/`.

## Siguiente fase

Cerrar importación/datasets (03) y anotación (04) con pruebas de permisos, archivos ZIP, duplicados, cajas y revisiones concurrentes.
