# Estado de implementación — HassLab

Actualización: 2026-10-22 (America/Lima). Rama: `feat/hasslab-implementacion`. PR: #1.

## Cómo retomar

1. Leer este archivo y el documento de la última fase en `docs/fases/`.
2. Consultar el head remoto y los resultados del CI del último commit; no asumir que un archivo escrito equivale a una funcionalidad validada.
3. Conservar cambios locales ajenos y trabajar por fase. Al terminar cada fase, actualizar este `.md`, registrar pruebas/limitaciones y subir un commit.
4. Dataset del usuario ya existente; Vue 3 + TypeScript + Tailwind. Django REST Framework/PostgreSQL. Docker al final.
5. No inventar precisión, recall, mAP, tiempos ni resultados de investigación.

## Estado por fase

| Fase | Estado y evidencia |
|---|---|
| 01. Arquitectura | Documento original en `docs/fase-01-arquitectura.md`; implementación agrupa dominio de investigación en `apps/research` y motor independiente en `backend/ai` |
| 02. Base, diseño y acceso | Backend/JWT/roles y build Vue/Tailwind verificados. CI PostgreSQL 17 aprobado. Smoke visual y navegación móvil aprobados en CI |
| 03. Dataset | Importación ZIP/YOLO/imágenes, galería y permisos implementados; pruebas aprobadas |
| 04. Anotación | Editor SVG, validación de cajas, revisión e historial implementados; pruebas API aprobadas |
| 05. Preprocesamiento | Originales intactos, recorte/letterbox/brillo/contraste, cajas y revisión de origen. Diez pruebas específicas aprobadas; worker real con Redis/PostgreSQL aprobado en CI de fase 05 |
| 06. Versiones | Snapshots, grupos train/val/test, ZIP YOLO y hashes de integridad. Seis pruebas específicas aprobadas; CI 39708069205 aprobado |
| 07. Entrenamiento | Implementado: lock CPU, entrenamiento YOLOv8 real, progreso, intentos, artefactos y modelos inactivos. Smoke local real aprobado; ver `docs/fases/07-entrenamiento.md` y cierre CI al final |
| 08. Inferencia | Código/pantallas escritos y pruebas con motor simulado. **Pendiente** validar con modelo YOLOv8 realmente entrenado |
| 09. Dashboard/reportes | Código/pantallas escritos; exportaciones XLSX/PDF de inspecciones verificadas por pruebas. Pendiente revisión funcional final |
| 10. Evaluación | Protocolo, muestras, observación manual, comparación pareada y exportación escritos; pruebas API aprobadas. Sin experimento científico realizado |
| 11. Documentación/calidad | README de instalación, suite y CI. Pendiente completar manuales, resolver advertencias restantes de OpenAPI y validación visual final |
| 12. Docker/despliegue | Pendiente; se hará al terminar validaciones locales |

## Checkpoints publicados

- `ea31137`: implementación transversal inicial, marcada WIP.
- `1eb56fd`: base, CI y autenticación. Run 39619785356 exitoso en PostgreSQL 17.
- `39294c9`: cierres 03–04, correcciones OpenAPI, suite ampliada y README de instalación.
- `fbe744e`: fase 05, revisión de origen en derivados y prueba real del worker. Run 39707473699: backend/frontend exitosos.
- Checkpoint fase 06: hashes del ZIP y del manifiesto, migración 0003, seis pruebas nuevas y smoke Playwright en CI. Consultar el head del PR para su SHA y resultados.

## Verificación al cerrar este checkpoint

- `pytest backend/tests -q`: **44 passed, 1 skipped**. SQLite aislado en local; el caso omitido requiere los servicios reales de CI.
- `manage.py check --settings=config.test_settings`: sin errores.
- `npm run build`: TypeScript/Vite correctos.
- `compileall backend`: correcto.
- CI fase 05: PostgreSQL 17, migraciones, suite con Redis/Celery real y build frontend correctos.
- Playwright: descarga local falló; ejecución real en GitHub Actions 39708069205 aprobada (login, colección, importación, revisión, navegación y ancho móvil). No se declara ejecución visual local.

## Próximo paso exacto

1. Revisar el cierre de fase 07 y el CI de su commit antes de continuar.
2. **Fase 08**: validar inferencia con pesos realmente entrenados, imágenes sin detecciones, coordenadas, tiempos y persistencia; no basta con el motor simulado.
3. El dataset de investigación y la GPU del usuario aún no están disponibles. No declarar métricas científicas con fixtures técnicos.
4. Completar fases 09–11; Docker permanece para fase 12.

## Archivos y migraciones de continuidad

- `backend/apps/research/migrations/0002_imagevariant_source_revision.py`: derivados antiguos con NULL necesitan regeneración antes de congelar.
- `0003_datasetversion_archive_sha256.py`: versiones antiguas sin hash necesitan nuevo snapshot.
- `backend/tests/test_worker_integration.py`: proceso Celery real habilitado con `REDIS_INTEGRATION=1`; requiere PostgreSQL/Redis.
- `frontend/tests/e2e/laboratory.spec.ts` y `scripts/smoke_server.py`: smoke con base temporal y datos sintéticos. Nunca usar ese servidor para investigación/producción.
- `README.md`: instalación local y ejecución de servidores/workers.

## Límites reales

Sin dataset del usuario ni pesos de investigación disponibles: no hay resultados científicos. JWT está en memoria y recargar exige nuevo login. El cegamiento de la inspección manual requiere organización del protocolo: el propietario también puede consultar etiquetas en otros módulos. Los tiempos de CPU/GPU deben medirse en el equipo objetivo. El relleno blanco no elimina el fondo original; eliminación automática de fondo y generación sintética de entrenamiento no están habilitadas.

## Corrección durante el smoke de navegador

Run 39707779885: backend y frontend correctos; el navegador detectó que el aviso de importación se borraba inmediatamente. `usePage.act` reemplazaba el mensaje específico con una cadena vacía al terminar. Corregido y protegido con tres pruebas unitarias de notificaciones. El smoke usa ahora nombres únicos por intento para no reutilizar colecciones de un intento anterior. Se separan los archivos Vitest de los de Playwright. El nuevo CI debe confirmar el flujo completo antes de pasar a fase 07.

## Cierre confirmado de sesión

- `9367e6e`: fase 06, integridad de snapshots y smoke de navegador.
- `f4df830`: corrección del aviso de importación; tres pruebas unitarias de UI.
- GitHub Actions **39708069205**: backend, frontend y browser-smoke **success**. Se validaron migraciones PostgreSQL, Redis/Celery real, pruebas, build y navegación móvil.
- No quedan cambios de código pendientes de subir de estas fases. Este commit solo registra el resultado del CI. Próximo trabajo: **fase 07**, entorno AI y entrenamiento mínimo técnico. Docker sigue pendiente para fase 12.

## Checkpoint fase 07 — 2026-10-22

- Entrenamiento real YOLOv8n preentrenado, dos épocas en CPU, con figuras geométricas sintéticas identificadas como prueba técnica: aprobado. Se recargaron los pesos generados; no son evidencia científica ni modelos aptos para inspeccionar paltas.
- Suite local en entorno worker nuevo: **53 passed, 2 skipped**; frontend **6 pruebas aprobadas** y build correcto. `pip check`, Django check y comprobación de migraciones correctos.
- Lock Linux/Python 3.12: PyTorch CPU 2.14.1, torchvision 0.29.1, Ultralytics headless 8.4.183; único proveedor OpenCV comprobado.
- Migración nueva: `0004_trainingrun_attempt_trainingrun_duration_seconds.py`.
- CI amplía la prueba real a PostgreSQL + Redis + proceso Celery separado. Consultar el resultado del commit de fase 07 antes de declararlo aprobado.
- El entorno local previo tenía binarios dañados; se creó `.venv-ai` limpio para las comprobaciones. No se incluye ningún entorno, imagen ni peso en Git.
