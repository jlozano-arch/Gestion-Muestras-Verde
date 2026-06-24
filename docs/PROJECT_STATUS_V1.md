# Project Status V1

## Indice

- [Resumen ejecutivo](#resumen-ejecutivo)
- [Tecnologia](#tecnologia)
- [Servidor y acceso](#servidor-y-acceso)
- [Repositorio Git](#repositorio-git)
- [Estado funcional](#estado-funcional)
- [Funcionalidades implementadas](#funcionalidades-implementadas)
- [Auditoria reciente del dashboard](#auditoria-reciente-del-dashboard)
- [Ultimos commits relevantes](#ultimos-commits-relevantes)
- [Pendientes conocidos](#pendientes-conocidos)
- [Ideas futuras](#ideas-futuras)

## Resumen ejecutivo

Proyecto: Gestion de Muestras Cafe Verde

La aplicacion permite registrar, consultar, comparar, catar, etiquetar, importar y administrar muestras comerciales de cafe verde para Indian Ecotrade. La V1 esta orientada al uso interno por navegador en red local, con SQLite como base de datos y almacenamiento persistente para archivos subidos.

## Tecnologia

- FastAPI
- SQLite
- SQLAlchemy
- Jinja2
- Docker
- ReportLab para PDFs
- OpenPyXL para lectura Excel
- QRCode para codigos QR

## Servidor y acceso

- Servidor: HP
- IP de referencia: `192.168.1.37`
- Puerto: `8000`
- URL de red local: `http://192.168.1.37:8000`
- Variable relevante: `APP_BASE_URL=http://192.168.1.37:8000`

## Repositorio Git

Remoto actual:

```text
origin https://github.com/jlozano-arch/Gestion-Muestras-Verde.git
```

## Estado funcional

Estado: V1 funcional.

La aplicacion esta preparada para operar en red local mediante Docker. El dashboard, las fichas de muestra, el comparador, las etiquetas Avery, el QR publico, la importacion Excel por staging y la limpieza administrativa estan implementados.

## Funcionalidades implementadas

- Gestion de muestras.
- Creacion, edicion y eliminacion individual de muestras.
- Edicion manual de estado.
- Estados validos: Recibida, Disponible, Enviada, Aprobada, Rechazada, Archivada.
- Catas con campos fisicos, sensoriales, notas y resultado.
- PDF de ficha de cata.
- Fotografias y documentos asociados a muestras y catas.
- Envios con descuento de stock disponible.
- Dashboard operativo.
- Comparador de muestras orientado a identidad comercial.
- Etiquetas Avery L7108REV con QR publico.
- QR publico de muestra en `/public/samples/{id}`.
- Importacion Excel con staging, previsualizacion, seleccion manual y aplicacion.
- Deteccion de duplicados basada en proveedor, referencia proveedor, CVC y contenedor.
- Eliminacion masiva de muestras.
- Limpieza administrativa de muestras.
- Ficha PDF completa de muestra en `/samples/{id}/pdf`.

## Auditoria reciente del dashboard

Se reviso que el dashboard se calcule desde la base de datos actual en cada peticion. No hay cache de dashboard ni variables persistentes para las metricas.

Metricas auditadas:

- Total muestras.
- Muestras por estado.
- Stock disponible.
- Muestras pendientes de catar.
- Muestras por origen con fallback a pais.
- Ultimas muestras.
- Ultimas catas.
- Muestras sin stock.

Se corrigio el calculo de muestras sin stock para tratar `NULL` como cero y se ajusto la logica de envio para actualizar estado usando gramos disponibles.

## Ultimos commits relevantes

```text
0832e39 Allow manual sample status editing
4449e00 Improve sample identifiers in dashboard and comparison
6ec62fa Improve public QR sample detail and visual badges
437faef Prioritize coffee identity across samples labels and QR
46d4f5a Improve generic Excel import and sample field labels
9c1c6e2 Add user guide and deployment checklist
2276e49 Add admin cleanup and public QR sample pages
e3c9023 Make sample filters data-driven
```

## Pendientes conocidos

- Revisar y eliminar codigo muerto heredado en funciones antiguas de PDF de cata.
- Completar capturas reales en la documentacion de usuario.
- Definir politica de permisos y autenticacion si la aplicacion se abre a mas usuarios.
- Revisar estrategia de backup automatizado.
- Ampliar pruebas automatizadas.

## Ideas futuras

- Integracion ERP Indian.
- Historial de cambios por usuario.
- Portal clientes.
- Exportaciones avanzadas.
- Migracion futura de SQLite a PostgreSQL.
- Almacenamiento de documentos/fotos desacoplado de la aplicacion.
