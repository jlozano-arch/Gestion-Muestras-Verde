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
- [Integracion ERP Indian](#integracion-erp-indian)
- [Notas para futuras integraciones ERP](#notas-para-futuras-integraciones-erp)

## Arquitectura general

Aplicacion monolitica FastAPI con vistas Jinja2, persistencia SQLAlchemy sobre SQLite y almacenamiento de archivos en disco. Docker expone la aplicacion en el puerto 8000.

Componentes principales:

- `app/main.py`: rutas, logica de negocio, importacion, PDFs, etiquetas y dashboard.
- `app/models.py`: modelos SQLAlchemy.
- `app/database.py`: configuracion de base de datos y migraciones ligeras.
- `app/erp_integration.py`: lectura opcional de datos ERP exportados por CVC.
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
- `ERP_SOURCE`: origen de datos ERP. Valores: `file` o `apps_script`.
- `ERP_DATA_PATH`: ruta opcional a un CSV o XLSX exportado del ERP Indian para consulta solo lectura por CVC.
- `ERP_APPS_SCRIPT_URL`: URL del Web App de Apps Script para consulta ERP solo lectura.

Ejemplo:

```text
APP_BASE_URL=http://192.168.1.37:8000
UPLOADS_DIR=uploads
ERP_DATA_PATH=/app/data/erp_indian.xlsx
ERP_SOURCE=apps_script
ERP_APPS_SCRIPT_URL=https://script.google.com/macros/s/XXXXXXXX/exec
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

## Integracion ERP Indian

La integracion ERP inicial esta implementada como una capa estrictamente de solo lectura. No escribe en el ERP, no modifica stock, no crea contratos, no aplica contratos y no escribe en Google Sheets.

Modulo:

```text
app/erp_integration.py
```

Funcion principal:

```text
get_erp_data_by_cvc(cvc: str) -> dict | None
```

Configuracion por archivo:

- Variable de entorno: `ERP_DATA_PATH`.
- Formatos soportados: CSV y XLSX.
- Fuente esperada: archivo exportado del ERP.
- Matching: coincidencia exacta por CVC normalizado.

Configuracion por Apps Script:

- `ERP_SOURCE=apps_script`.
- `ERP_APPS_SCRIPT_URL` apunta al Web App publicado dentro del ERP/TRACER.
- Endpoint esperado: `GET ?action=getDatosMuestraERP&cvc=53-2026CVC`.
- La consulta es solo lectura y no depende de la interfaz TRACER.
- El endpoint busca directamente en la hoja `LARGOS`.
- Datos confirmados de `LARGOS`: cabecera en fila 3, datos desde fila 4 y CVC en columna C con encabezado `CTR. COMPRA`.
- Si Apps Script no esta configurado o devuelve error tecnico, la app muestra `ERP no disponible`.

Ejemplo de configuracion en `.env` o Docker Compose:

```text
ERP_SOURCE=apps_script
ERP_APPS_SCRIPT_URL=https://script.google.com/macros/s/XXXXXXXX/exec
```

Estados devueltos:

- `not_configured`: no existe `ERP_DATA_PATH` o el archivo no se puede leer.
- `no_cvc`: la muestra no tiene CVC.
- `found`: una coincidencia unica.
- `multiple`: varias filas con el mismo CVC.
- `not_found`: se representa como `None` cuando no hay coincidencias.

Campos privados visibles en `/samples/{id}` cuando hay coincidencia:

- CVC.
- Proveedor ERP.
- Calidad ERP.
- Pais/origen ERP.
- Almacen ERP.
- Sacos comprados.
- Kg comprados.
- Sacos disponibles.
- Kg disponibles.
- Precio compra.
- Fecha contrato.
- Estado contrato.

Campos publicos limitados visibles en `/public/samples/{id}`:

- Calidad ERP.
- Pais/origen ERP.
- Almacen ERP.
- Kg disponibles.
- Estado contrato.

La vista publica no muestra precio de compra.

## Notas para futuras integraciones ERP

- La integracion actual es solo lectura y debe mantenerse asi salvo decision explicita de proyecto.
- Mantener `Sample.code` como codigo interno.
- Usar identidad comercial para integraciones: proveedor, referencia proveedor, CVC y contenedor.
- No acoplar importadores a rutas locales del portatil.
- Preparar migracion a PostgreSQL si aumenta concurrencia o multiusuario.
- Mantener `uploads` y base de datos en volumen persistente.
