# HassLab

Sistema web de investigación para detectar roña superficial en paltas Hass con YOLOv8.

**Estado:** implementación por fases. Revisar [docs/PROGRESO.md](docs/PROGRESO.md) antes de continuar. El código está en la rama `feat/hasslab-implementacion`; el PR de seguimiento es #1. Los módulos de IA requieren instalar el entorno worker y aportar un dataset revisado. No se incluyen imágenes de investigación, contraseñas ni modelos entrenados.

## Stack

Vue 3 + TypeScript + Tailwind CSS, Django REST Framework, PostgreSQL, Celery y Redis. El motor AI reside en `backend/ai/`. Docker se incorpora al final de las validaciones locales.

## Inicio local (Windows PowerShell)

Requisitos: Git, Python 3.12, Node 22.12+ y PostgreSQL 17. Redis/Celery se ejecutan en WSL2 o Linux. Frontend y backend son aplicaciones independientes dentro del mismo repositorio.

```powershell
git clone -b feat/hasslab-implementacion https://github.com/mechananthony22/ProyectoTesis__Yolo.git
cd ProyectoTesis__Yolo
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copia el valor generado a `SECRET_KEY` en `.env`. Configura también la contraseña PostgreSQL, base y usuario. Nunca subas `.env` a Git.

En pgAdmin o `psql`, conectado como administrador de PostgreSQL, crea la cuenta/base; reemplaza la contraseña de ejemplo:

```sql
CREATE USER hasslab WITH PASSWORD 'cambia-esta-clave';
CREATE DATABASE hasslab OWNER hasslab;
```

Configura `POSTGRES_DB=hasslab`, `POSTGRES_USER=hasslab` y la contraseña elegida en `.env`. Luego:

```powershell
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

En otra terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abre `http://localhost:5173`. Inicia sesión con el superusuario creado. No hay cuentas ni contraseñas predeterminadas. Swagger: `http://localhost:8000/api/v1/docs/`.

## Procesamientos en segundo plano

En Linux/WSL2, crea su propio entorno Python para el backend; no reutilices el entorno Windows. Instala las mismas dependencias y usa el mismo PostgreSQL, archivos y configuración que el backend. En WSL2, `localhost` de PostgreSQL puede requerir cambiar `POSTGRES_HOST` a la dirección del host Windows; comprueba la conectividad.

Inicia Redis con tu instalación local y ejecuta, desde `backend/`:

```bash
celery -A config worker -Q preprocessing --concurrency=1 --loglevel=info
```

El worker CPU tiene un lock independiente, probado en Linux x86_64 con Python 3.12. Crea un entorno nuevo (no mezcles dependencias del servidor ni del entorno Windows):

```bash
python3.12 -m venv .venv-ai
source .venv-ai/bin/activate
python -m pip install -r backend/requirements/worker-cpu.lock
python -m pip check
```

Incluye PyTorch 2.14.1+cpu, torchvision 0.29.1+cpu y Ultralytics headless 8.4.183 con un único proveedor OpenCV. El lock instala también Django y Celery. Comparte con el servidor PostgreSQL, Redis, `storage/media/` y el archivo `AI_RESOURCE_LOCK`; los procesos deben ver los mismos archivos. No instales además `ultralytics` u otro OpenCV en este entorno. El detector inicialmente admite solo la clase `0: rona`.

Para GPU, utiliza la pareja oficial PyTorch/torchvision compatible con tu CUDA y el lock común en un entorno separado; aún no se ha validado hardware GPU. Ver [fase 07](docs/fases/07-entrenamiento.md).

Con el entorno AI preparado, ejecuta un worker de IA:

```bash
celery -A config worker -Q training,inference --concurrency=1 --loglevel=info
```

`AI_DEVICE=cpu` es el valor inicial. Cambia a GPU solo después de verificar PyTorch/CUDA. Los trabajos y errores se consultan en la pantalla Trabajos. Si Redis no está disponible, el registro queda en cola y se puede reenviar.

## Flujo de trabajo

1. Registrar una colección e importar el dataset existente (imágenes o ZIP YOLO).
2. Revisar las cajas, estados y códigos de fruto/grupo.
3. Mantener las particiones importadas o distribuir por grupo de fruto.
4. Opcionalmente generar y revisar derivados preprocesados.
5. Congelar una versión reproducible y exportable.
6. Entrenar, revisar métricas de validación y activar un modelo como administrador.
7. Realizar inspecciones, revisar resultados y descargar reportes.
8. Ejecutar el protocolo experimental sobre test independiente y las mismas muestras manuales.

No hay transferencia automática de predicciones al dataset. «Sin detecciones» no significa «fruto sano». Las métricas científicas requieren experimentos reales.

## Comprobaciones

Desde la raíz, con el entorno Python activado:

```bash
python -m pytest -q
python backend/manage.py check
python -m pip check
```

`pytest` usa SQLite aislado por defecto. GitHub Actions ejecuta la suite y migraciones también contra PostgreSQL 17. Para probar con PostgreSQL local y permisos de crear bases de prueba: `pytest --ds=config.ci_settings`.

```bash
cd frontend
npm run build
```

## Datos y seguridad

Los archivos se guardan bajo `storage/media/` y no se versionan. La API sirve imágenes mediante JWT y permisos de propietario. El administrador accede a todas las colecciones. Conserva copia tanto de PostgreSQL como de `storage/`; una copia solo de la BD no incluye imágenes ni pesos.

Los tokens se conservan en memoria: al recargar la página debes volver a iniciar sesión. Esto evita persistir tokens en `localStorage`. La configuración de producción, HTTPS, restauración de respaldos y Docker se validarán en su fase final.
