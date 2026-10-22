# Fase 05 — Preprocesamiento y trazabilidad

## Implementado

- Procesar imágenes seleccionadas en segundo plano con Celery.
- Redimensionar a 640/800 con proporción conservada y relleno blanco constante.
- Recorte normalizado, brillo y contraste moderados.
- Transformación y recorte de las cajas junto con la imagen.
- Conservar el original, hash, receta, tamaño y revisión de etiquetas de cada derivado.
- Visor antes/después con cajas del derivado.
- Rechazar recortes vacíos, valores no finitos y parámetros fuera de rango.
- Rechazar derivados obsoletos para entrenamiento si cambiaron sus etiquetas originales.

## Verificado

Diez pruebas específicas aprobadas: original intacto, fondo blanco, coordenadas transformadas, revisión de origen, rechazo de derivado obsoleto, rechazo de train sin lesiones después del recorte, ZIP coherente, parámetros inválidos, imagen pequeña y fallo por hash alterado. También se conserva la prueba de idempotencia del trabajo.

Estas son pruebas de código con imágenes sintéticas simples; no son resultados de investigación ni una validación de calidad de roña.

## Redis y worker real

Se incorpora una prueba CI que lanza un proceso Celery real, publica en Redis y verifica la creación del derivado en PostgreSQL. Solo se habilita con `REDIS_INTEGRATION=1`. Resultado confirmado: GitHub Actions run 39707473699 completó backend y frontend con éxito, incluyendo el caso de worker real habilitado. La prueba local se omite si faltan los servicios.

## Alcance

El relleno blanco no elimina el fondo original. La eliminación automática del fondo no se habilita todavía porque requiere comprobar que conserva la textura y las lesiones. No se usa relleno generativo ni se duplican partes de la palta.

## Siguiente paso

Fase 06: consolidar y verificar versiones de originales/derivados, particiones y exportación YOLO. La revisión de cada derivado sigue siendo explícita antes de congelar.
