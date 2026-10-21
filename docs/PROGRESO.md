# Estado de implementación — HassLab

Última actualización: 2026-10-21 (America/Lima).
Rama de trabajo: `feat/hasslab-implementacion`.

## Instrucciones de continuidad

1. Leer este archivo y `docs/fase-01-arquitectura.md` antes de continuar.
2. Revisar `git status` y no sobrescribir cambios ajenos.
3. Trabajar por fase. Al terminar una fase, anotar archivos, pruebas reales, limitaciones y siguiente paso; hacer commit y subirlo a GitHub.
4. No llamar «terminada» a una fase por tener archivos: verificar sus flujos.
5. No inventar precisión, recall, mAP, tiempos ni resultados de la tesis.
6. El usuario ya tiene dataset; el sistema lo importa y administra. Vue 3 + TypeScript + Tailwind CSS. Backend Django REST Framework y PostgreSQL. Docker al final.

## Checkpoint 01: implementación inicial en revisión

Se ha escrito un primer corte transversal del sistema. Está **en desarrollo**, no validado integralmente. Se conserva en Git para poder continuar sin perder trabajo. `main` conserva la planificación aprobada; la implementación se revisa en esta rama.

| Fase | Estado | Código preparado |
|---|---|---|
| 01. Planificación | Documentada; actualizar decisiones de implementación | Documento original y este seguimiento |
| 02. Base, diseño y acceso | Implementada, pendiente de pruebas de integración | Django settings, usuario/roles/JWT, migraciones, Vue/Router/Pinia/Tailwind, layout y login |
| 03. Importación y dataset | Implementada, pendiente de pruebas | API importación ZIP/imágenes, galería, duplicados, procedencia y permisos |
| 04. Anotaciones | Implementada, pendiente de pruebas | Editor SVG, cajas normalizadas, revisión humana, historial |
| 05. Preprocesamiento | Implementada, pendiente de pruebas del worker | Letterbox, recorte/brillo/contraste, derivados y transformación de cajas |
| 06. Versiones del dataset | Implementada, pendiente de pruebas | Split por grupo, snapshots, manifiestos y ZIP YOLO |
| 07. Entrenamiento | Integración escrita; sin entrenamiento real | Celery, YOLOv8, epochs/métricas/modelos y exclusión de recursos AI |
| 08. Detección e historial | Integración escrita; pendiente de pruebas | Carga/lotes/cámara, inferencia, revisión e historial |
| 09. Dashboard/reportes | Implementada, pendiente de pruebas | Estadísticas reales, gráficos, exportación de inspecciones XLSX/PDF |
| 10. Evaluación experimental | Implementación parcial | Protocolo, muestras test, observación manual, evaluación YOLO, resumen pareado; falta exportación de evidencia |
| 11. Pruebas/documentación | En curso | `manage.py check` sin errores; faltan pruebas API/servicios, build final, manuales y CI |
| 12. Docker/despliegue | No iniciada | Se hará después de validar el funcionamiento local |

## Arquitectura implementada

- `frontend/src/views/`: pantallas por módulo, con Tailwind.
- `frontend/src/components/`: editor de cajas, imagen privada, estados y avisos.
- `frontend/src/services/`: cliente API, descarga y manejo de errores.
- `backend/apps/accounts/`: usuarios, roles y perfil.
- `backend/apps/research/`: dominio de investigación, serializers, servicios, API y tareas.
- `backend/ai/`: procesamiento/inferencia/evaluación sin dependencia de las vistas HTTP.
- Se agrupan inicialmente las entidades de investigación en una app Django para mantener las transacciones y relaciones coherentes. Las pantallas y servicios mantienen responsabilidades diferenciadas; evitar crear apps vacías.

## Verificado hasta este checkpoint

- Instalación del entorno Python 3.12 y dependencias web realizada; versiones resueltas en `backend/requirements.txt`.
- `python backend/manage.py check --settings=config.test_settings`: sin errores.
- Generadas migraciones iniciales para usuario personalizado y dominio de investigación.
- Dependencias frontend instaladas y `package-lock.json` generado.
- Build frontend lanzado, resultado pendiente de recuperar/repetir. No asumir que pasó.
- No se ha probado PostgreSQL, Redis, Celery ni YOLO real todavía.

## Próximo paso exacto

1. Ejecutar `cd frontend && npm run build` y corregir errores TypeScript.
2. Añadir pruebas críticas del backend: permisos entre usuarios, ZIP seguro, anotaciones, revisiones, snapshots, división por fruto, tareas y exportaciones.
3. Completar exportación `GET /api/v1/evaluations/{id}/export/`, que la interfaz ya invoca.
4. Validar entorno PostgreSQL y migraciones; SQLite se usa solo en pruebas aisladas.
5. Revisar OpenAPI, errores HTTP, dependencias AI (OpenCV headless/Ultralytics) y pruebas visuales del frontend.
6. Cerrar fase 02 con evidencia, continuar cierres de fases 03–10 y documentar límites reales.
7. Crear README/manuales/CI. Docker al final.

## Límites que no deben confundirse con resultados

- Sin dataset del usuario ni pesos entrenados disponibles: no hay resultados científicos.
- Tokens JWT en memoria: recargar la página obliga a iniciar sesión; documentado en Configuración.
- La observación manual presenta muestras sin referencia/predicción, pero el dueño del dataset puede consultar sus anotaciones en otro módulo. El cegamiento experimental requiere organización de participantes y protocolo.
- Las pruebas de latencia y de GPU deben realizarse en el equipo objetivo.
