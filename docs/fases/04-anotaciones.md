# Fase 04 — Revisión y anotación de roña

## Implementado

Editor SVG sobre la imagen, dibujo con mouse/táctil, edición numérica normalizada, eliminación de cajas, clase 0, estados pendiente/sin lesiones/con roña/descartada, historial con autor y revisión.

Las revisiones emplean control de concurrencia: una petición con número de revisión anterior se rechaza. No se sobrescribe una versión congelada del dataset.

## Verificado

Se rechazan coordenadas negativas, NaN, cajas fuera de imagen y clases distintas de 0. «Sin lesiones» exige cero cajas; «Con roña» exige cajas. Una revisión concurrente no sobrescribe otra. Estas pruebas pasan junto con la suite de dataset.

## Alcance de revisión humana

El usuario que guarda un estado revisado queda registrado. La competencia del revisor y el apoyo de un especialista son parte del protocolo de investigación, no una inferencia del software.

## Siguiente paso

Validar las transformaciones del preprocesamiento (fase 05), manteniendo originales y trazabilidad de la revisión usada por cada derivado.
