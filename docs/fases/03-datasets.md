# Fase 03 — Importación y administración del dataset existente

## Implementado

- Registrar colecciones con nombre, descripción, origen y licencia.
- Importar JPG/JPEG/PNG/WEBP y ZIP con imágenes/etiquetas YOLO.
- Conservar train/val/test importados (`valid` se normaliza a `val`).
- Galería paginada, búsqueda, estados, metadatos y archivos privados.
- Deduplicación exacta SHA-256 por colección y sugerencias de similitud dHash.
- Asignación de código de fruto/grupo, procedencia y partición por imagen.
- Las etiquetas importadas quedan pendientes de revisión; una etiqueta vacía no confirma sanidad.

## Verificado

Pruebas de importación YOLO, duplicados, permisos entre usuarios y rechazo de rutas ZIP peligrosas aprobadas. La suite de dataset/anotación/versiones suma 12 casos aprobados.

## Formato de importación

ZIP: `images/train/a.jpg` junto a `labels/train/a.txt`; también se admite `train/images/a.jpg` con `train/labels/a.txt`. Única clase: `0 rona`. Importar archivos sueltos sirve para imágenes sin etiquetas; para conservar etiquetas usar ZIP.

Límites: carga total 100 MB, 20 MB por imagen, 25 millones de píxeles, 250 MB descomprimidos y 2000 imágenes por carga. No se extraen rutas del usuario al sistema de archivos.

## Siguiente paso

Revisar etiquetas en fase 04. Antes de particionar, identificar fotos del mismo fruto. dHash sugiere similitud, no reemplaza esa identificación.
