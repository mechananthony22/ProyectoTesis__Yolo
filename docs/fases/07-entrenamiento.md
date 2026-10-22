# Fase 07 — Entrenamiento YOLOv8

Fecha: 2026-10-22. Estado: implementación y entrenamiento técnico CPU local verificados; resultado de CI registrado en `../PROGRESO.md`.

## Implementación

- `backend/ai/training.py`: adaptador independiente de Django. Transferencia desde pesos oficiales YOLOv8n/YOLOv8s, hiperparámetros permitidos, semilla, dispositivo CPU o GPU configurada por el servidor y callback por época.
- `apps/research/tasks.py`: ejecución Celery, exclusión de recursos compartidos y persistencia. Un trabajo ejecutado no se duplica; reintentos guardan directorios independientes. Los errores conservan archivos y mensaje.
- `TrainingRun`: número de intento y duración; migración 0004. Cada intento registra configuración efectiva, versiones, hardware, commit del código, hashes del dataset y pesos base, métricas, épocas y archivos.
- API de artefactos protegida por propietario/administrador, rutas seguras y selección del intento. Progreso y heartbeat persistentes.
- Vue/Tailwind: formulario, CPU/dispositivo del servidor, gráfico por época, duración, intentos y descargas. Una métrica ausente o no finita se muestra como «No medida», nunca como un cero inventado.
- Al terminar se registra un modelo **inactivo**. Activarlo sigue siendo una decisión administrativa. Las métricas finales corresponden a validación del mejor modelo; el conjunto test queda reservado para evaluación independiente.

Directorio de cada intento: `storage/media/training-artifacts/<run>/attempt-N/fit/`. Incluye `best.pt`, `last.pt`, `results.csv`, gráficos, `console.log`, `training.jsonl`, `experiment.json` y `metrics.json`; si falla, `failure.json` conserva el error. El motor solo carga pesos oficiales o generados por el sistema; no acepta archivos de pesos arbitrarios de usuarios.

## Entorno reproducible CPU

Linux x86_64, Python 3.12. En la raíz:

```bash
python3.12 -m venv .venv-ai
source .venv-ai/bin/activate
python -m pip install -r backend/requirements/worker-cpu.lock
python -m pip check
python backend/manage.py migrate
cd backend
celery -A config worker -Q training,inference --concurrency=1 --loglevel=info
```

El lock del worker es completo e independiente de `requirements.txt`: úsalo directamente en un entorno nuevo. Se comprobó PyTorch 2.14.1+cpu, torchvision 0.29.1+cpu, Ultralytics headless 8.4.183 y OpenCV headless 5.0.0.93. No mezclar las distribuciones estándar y headless de Ultralytics/OpenCV. El servidor web conserva su entorno base ligero.

Servidor y worker necesitan el mismo PostgreSQL/Redis, originales, snapshots, artefactos y bloqueo. Configura `.env` según README. `AI_DEVICE=cpu` por defecto. `AI_BASE_WEIGHTS_DIR` permite una caché de pesos oficiales y `AI_RESOURCE_LOCK` un bloqueo compartido entre procesos del mismo host. No es un bloqueo distribuido entre hosts con discos distintos.

La primera ejecución necesita descargar pesos oficiales y disponer de espacio suficiente; los entrenamientos posteriores los reutilizan. Para GPU, instala una pareja PyTorch/torchvision indicada por el selector oficial, más `worker-common.lock` en un entorno separado, y valida CUDA en el hardware objetivo. **No se declara GPU verificada**. Fuentes: [PyTorch](https://pytorch.org/get-started/locally/), [Ultralytics headless](https://docs.ultralytics.com/quickstart/), [callbacks](https://docs.ultralytics.com/usage/callbacks/).

## Cómo revisar desde la interfaz

1. Importar el dataset existente, revisar anotaciones y agrupar por fruto.
2. Separar train/val/test y congelar una versión íntegra (fase 06).
3. En Entrenamientos elegir versión, YOLOv8n o YOLOv8s y parámetros; comenzar con CPU y recursos modestos.
4. Consultar Trabajos, épocas, progreso y errores; descargar archivos del intento.
5. Comprobar el modelo registrado y sus métricas de validación. No activar un modelo de prueba geométrica para inspecciones reales.

## Verificaciones y límites

- Suite local: 53 aprobadas, 2 omitidas por requerir servicios/opt-in; frontend 6 aprobadas y build correcto. Django check y migraciones sin diferencias.
- Prueba real local: dos épocas de YOLOv8n preentrenado sobre figuras geométricas (4 train, 2 val, 2 test). Comprueba pesos recargables, hashes, archivos, progreso y métricas JSON válidas. **No contiene imágenes de paltas ni resultados de la tesis**.
- Se detectó que Ultralytics vuelve a invocar el callback final al evaluar los mejores pesos. Se emparejan callbacks de inicio/fin para no registrar una época inexistente; prueba de regresión incluida.
- Casos unitarios: concurrencia, errores, reintentos, permisos, rutas de archivos, dispositivos permitidos y métricas ausentes.
- GitHub Actions incorpora `training-smoke`: instalación limpia, PostgreSQL 17, Redis y worker Celery real separado. Publica un informe técnico sin métricas científicas. Ver su resultado final en PROGRESO.

Prueba local optativa, desde la raíz y con el entorno worker activo:

```bash
AI_SMOKE=1 AI_BASE_WEIGHTS_DIR="$PWD/storage/base-weights" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m pytest backend/tests/test_training_smoke.py -q
```

La variante asíncrona requiere PostgreSQL con permisos de crear base de pruebas y Redis: añade `REDIS_INTEGRATION=1` y `--ds=config.ci_settings`. La prueba utiliza una base aislada y fixtures; no se ejecuta contra datos de producción.

Pendiente: entrenamiento sobre dataset revisado del usuario, validación de GPU, pruebas con más volumen y protocolo científico. Fase 08 validará la inferencia con pesos reales. Docker se mantiene para fase 12.
