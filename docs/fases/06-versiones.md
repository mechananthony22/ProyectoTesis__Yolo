# Fase 06 — Versiones reproducibles y exportación YOLO

## Implementado

- Conservar particiones importadas o distribuir grupos completos por fruto con semilla fija.
- Rechazar versiones con imágenes pendientes, sin código de grupo o con grupos repartidos entre train/val/test.
- Congelar originales o derivados aceptados, etiquetas normalizadas, revisión, revisor, split y hashes.
- Generar ZIP con `images/{split}`, `labels/{split}`, `data.yaml` y `manifest.json`.
- Guardar SHA-256 del manifiesto y del ZIP completo.
- Comprobar integridad antes de descargar o desempaquetar un snapshot para IA.
- Rechazar cambios en imágenes, etiquetas o manifiesto, y versiones antiguas sin hash del ZIP.

## Verificado

Seis pruebas específicas aprobadas: descarga/desempaquetado correcto, ZIP corrupto, etiquetas modificadas, manifiesto alterado, permisos de propietario y versión antigua sin hash. Se suman a las pruebas existentes de split por fruto, negativos revisados y snapshots intactos después de cambiar anotaciones.

Suite local completa: **44 aprobadas, una omitida**. La omitida requiere PostgreSQL/Redis reales y se habilita en CI. Build frontend y `manage.py check` correctos.

CI de la fase anterior (run 39707473699): backend y frontend exitosos, con PostgreSQL 17, Redis y el test que inicia un proceso Celery real. El CI de este checkpoint debe comprobar también la nueva migración 0003.

## Migración

`0003_datasetversion_archive_sha256.py` añade el hash del ZIP. Las versiones antiguas sin ese dato permanecen registradas, pero se exige congelar una nueva versión antes de usarlas. No se inventa un hash ni se modifica evidencia antigua para hacerla pasar por verificada.

## Comprobación visual

Se añade un smoke test Playwright para login, registro de colección, importación de imagen sintética, revisión, navegación y ancho móvil. Se ejecutará en GitHub Actions. El navegador no se pudo descargar en el entorno local; no se declara validación visual local.

## Próximo paso exacto

Fase 07: resolver y fijar dependencias AI compatibles (PyTorch/torchvision/Ultralytics/OpenCV), ejecutar un entrenamiento técnico mínimo reproducible y revisar progreso, guardado de pesos y métricas. Ningún resultado de ese smoke test se usará como resultado de la tesis. El entrenamiento de investigación necesita el dataset real del usuario y el hardware objetivo.
