# Manual Tecnico

## Indice

- [Arquitectura general](#arquitectura-general)
- [Estructura de carpetas](#estructura-de-carpetas)
- [Modelos principales](#modelos-principales)
- [Estados validos](#estados-validos)
- [Flujo de importacion Excel](#flujo-de-importacion-excel)
- [Matching de importacion](#matching-de-importacion)
- [Despliegue](#despliegue)
- [Docker](#docker)
- [Variables de entorno](#variables-de-entorno)
- [Rutas principales](#rutas-principales)
- [Sistema de QR](#sistema-de-qr)
- [Sistema de etiquetas Avery](#sistema-de-etiquetas-avery)
- [PDFs](#pdfs)
- [Dashboard](#dashboard)
- [Notas para futuras integraciones ERP](#notas-para-futuras-integraciones-erp)

## Arquitectura general

Aplicacion monolitica FastAPI con vistas Jinja2, persistencia SQLAlchemy sobre SQLite y almacenamiento de archivos en disco. Docker expone la aplicacion en el puerto 8000.

Componentes principales:

- `app/main.py`: rutas, logica de negocio, importacion, PDFs, etiquetas y dashboard.
- `app/models.py`: modelos SQLAlchemy.
- `app/database.py`: configuracion de base de datos y migraciones ligeras.
- `app/templates/`: HTML Jinja2.
- `app/static/`: CSS, logo y recursos estaticos.
- `uploads/`: documentos/fotos subidos.
- `data/`: base SQLite y PDFs/pruebas locales si se generan.

## Estructura de carpetas

```text
app/
  main.py
  models.py
  database.py
  countries.py
  templates/
  static/
uploads/
data/
docs/
```

## Modelos principales

### Sample

Representa una muestra de cafe verde. Campos relevantes:

- `code`.
- `country_code`.
- `country_name`.
- `origin`.
- `producer`.
- `supplier_reference`.
- `provider_sample_number`.
- `container_number`.
- `purchase_contract_cvc`.
- `sales_contract_cvv`.
- `quality`.
- `warehouse`.
- `sample_type`.
- `category`.
- `commercial_result`.
- `harvest_date`.
- `variety`.
- `altitude`.
- `processing`.
- `physical_location`.
- `received_quantity_g`.
- `available_quantity_g`.
- `status`.
- `notes`.

Relaciones:

- `tastings`.
- `shipments`.
- `events`.
- `documents`.

### Tasting

Representa una cata. Incluye datos fisicos, sensoriales, puntuaciones, resultado, notas y recomendaciones.

### Document

Representa archivo o fotografia asociado a una muestra y opcionalmente a una cata.

### Shipment

Representa envio de muestra. Al registrar envio se descuenta cantidad disponible.

## Estados validos

Valores internos:

- `received`
- `available`
- `approved`
- `rejected`
- `shipped`
- `archived`

Etiquetas visibles:

- Recibida
- Disponible
- Aprobada
- Rechazada
- Enviada
- Archivada

## Flujo de importacion Excel

Rutas:

- `GET /imports`
- `POST /imports/preview`
- `GET /imports/{batch_id}`
- `POST /imports/{batch_id}/apply`
- `POST /imports/{batch_id}/delete-created`

La importacion no crea muestras directamente en la previsualizacion. Primero crea `ImportBatch` e `ImportRow`, normaliza datos y propone acciones.

## Matching de importacion

Identidad actual:

- proveedor
- referencia proveedor
- CVC
- contenedor

Reglas:

- Si no hay referencia proveedor, la fila queda incompleta.
- No se usa productor, origen o calidad para update automatico.
- CVC invalido se trata como nulo.
- Contenedor ayuda a distinguir muestras con misma referencia/CVC.

## Despliegue

Actualizar codigo:

```bash
git pull
docker compose up -d --build
```

Acceso:

```text
http://192.168.1.37:8000
```

## Docker

La aplicacion se ejecuta con Docker Compose. El servicio expone `0.0.0.0:8000`, lo que permite acceso desde otros equipos de la red si el firewall lo permite.

## Variables de entorno

- `APP_BASE_URL`: base URL usada para QR publicos.
- `UPLOADS_DIR`: carpeta de documentos/fotos subidos.

Ejemplo:

```text
APP_BASE_URL=http://192.168.1.37:8000
UPLOADS_DIR=uploads
```

## Rutas principales

- `/`
- `/samples`
- `/samples/new`
- `/samples/{id}`
- `/samples/{id}/edit`
- `/samples/{id}/pdf`
- `/samples/{id}/label`
- `/samples/{id}/tastings`
- `/samples/{id}/tastings/{tasting_id}/pdf`
- `/compare`
- `/labels`
- `/labels/pdf`
- `/public/samples/{id}`
- `/imports`
- `/imports/{batch_id}`
- `/admin/clean-samples`

## Sistema de QR

Los QR usan:

```text
{APP_BASE_URL}/public/samples/{sample_id}
```

La vista publica es de solo lectura y no permite editar ni borrar.

## Sistema de etiquetas Avery

Modelo implementado:

- Avery L7108REV.
- Hoja A4 vertical.
- Matriz 3 x 3.
- Etiqueta fisica 62 x 89 mm.
- Diseno interno horizontal rotado.
- Posicion inicial configurable de 1 a 9.
- Copias configurables.

La etiqueta muestra identidad de cafe, bandera/colores por origen, calidad, tipo, referencia proveedor, CVC y QR.

## PDFs

PDFs implementados:

- Etiquetas Avery.
- Ficha de cata.
- Ficha completa de muestra en `/samples/{id}/pdf`.

La ficha completa incluye cabecera corporativa, QR publico, datos comerciales, datos de origen, catas, fotografias y documentos.

## Dashboard

El dashboard recalcula las metricas desde la base en cada peticion. No usa cache.

Se auditan:

- Total de muestras.
- Estados.
- Stock disponible.
- Muestras pendientes de catar.
- Muestras sin stock.
- Ultimas muestras.
- Ultimas catas.
- Muestras por origen con fallback a pais.

## Notas para futuras integraciones ERP

- Mantener `Sample.code` como codigo interno.
- Usar identidad comercial para integraciones: proveedor, referencia proveedor, CVC y contenedor.
- No acoplar importadores a rutas locales del portatil.
- Preparar migracion a PostgreSQL si aumenta concurrencia o multiusuario.
- Mantener `uploads` y base de datos en volumen persistente.
