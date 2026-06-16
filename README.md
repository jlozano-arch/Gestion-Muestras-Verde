# Gestión de Muestras de Café Verde - Indian Ecotrade

Aplicación FastAPI para la gestión integral de muestras de café verde de Indian Ecotrade.

## Características

- **Registro de Muestras**: Registro detallado de cada muestra de café verde
- **Catas**: Evaluación completa con cribas, humedad, defectos, notas y valoración
- **Documentación**: Subida de fotos y documentos de soporte
- **Envíos**: Control de envíos con descuento automático de cantidad disponible
- **Etiquetas PDF**: Generación de etiquetas con QR y bandera del país
- **Dashboard**: Panel de control con métricas y estado general
- **Resultado Comercial**: Análisis de viabilidad comercial
- **Timeline**: Histórico de eventos para cada muestra
- **Evaluación de Compra**: Puntuación comercial y técnica
- **Indian Score**: Puntuación 0-100 propia de Indian Ecotrade
- **Comparador**: Comparación lado a lado de múltiples muestras
- **Importador Excel**: Importación masiva de datos desde Excel
- **Tests**: Cobertura de funcionalidades básicas

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Desarrollo

```bash
make run
```

### Docker

```bash
docker-compose up
```

### Tests

```bash
make test
```

## Estructura de Directorios

```
Gestion-Muestras-Verde/
├── app/
│   ├── main.py           # Aplicación principal
│   ├── models.py         # Modelos de datos SQLAlchemy
│   ├── database.py       # Configuración de BD
│   ├── countries.py      # Datos de países y banderas
│   ├── templates/        # Plantillas HTML
│   └── static/           # CSS, JS, imágenes
├── scripts/
│   ├── import_excel.py   # Importador de Excel
│   └── seed.py           # Datos iniciales
├── tests/
│   └── test_app.py       # Tests funcionales
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── Makefile
└── .github/workflows/
```

## API Endpoints

- `GET /` - Dashboard principal
- `GET/POST /samples` - Lista y creación de muestras
- `GET/POST /samples/{id}` - Detalle y edición de muestra
- `GET/POST /samples/{id}/tastings` - Catas
- `POST /samples/{id}/shipments` - Registrar envíos
- `GET /samples/{id}/labels` - Generar etiquetas PDF
- `GET /samples/{id}/events` - Timeline de eventos
- `GET /compare` - Comparador de muestras
- `POST /import` - Importar desde Excel

## Configuración

Variables de entorno:
- `DATABASE_URL` - URL de conexión a BD
- `APP_BASE_URL` - Base URL para los QR en etiquetas PDF
- `UPLOADS_DIR` - Directorio de uploads para documentos y fotos
- `SECRET_KEY` - Clave secreta de la aplicación
- `DEBUG` - Modo debug (true/false)

Ejemplo de archivo de entorno:

```bash
cp .env.example .env
```

### Docker

El `docker-compose.yml` monta los volúmenes:

- `./data:/app/data` para la base de datos SQLite persistente
- `./uploads:/app/uploads` para documentos y fotos persistentes

Si quieres exponer la app en la red local, ajusta `APP_BASE_URL` a la URL pública del servidor, por ejemplo:

```bash
APP_BASE_URL=http://192.168.1.100:8000
```

## Licencia

Indian Ecotrade © 2026
