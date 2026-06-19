# Guia de usuario

## Gestion de Muestras de Cafe Verde

**Indian Ecotrade**

**Version actual:** aplicacion local con gestion de muestras, catas, importaciones Excel, etiquetas Avery, QR publicos y administracion de limpieza.

**Fecha de generacion:** 19 de junio de 2026.

**Documento:** guia funcional para usuarios finales.

---

## Indice

1. [Introduccion](#1-introduccion)
2. [Acceso a la aplicacion](#2-acceso-a-la-aplicacion)
3. [Dashboard](#3-dashboard)
4. [Gestion de muestras](#4-gestion-de-muestras)
5. [Estados de muestra](#5-estados-de-muestra)
6. [Busqueda y filtros](#6-busqueda-y-filtros)
7. [Gestion de catas](#7-gestion-de-catas)
8. [Fotografias y documentos](#8-fotografias-y-documentos)
9. [Etiquetas](#9-etiquetas)
10. [QR publicos](#10-qr-publicos)
11. [Importacion Excel](#11-importacion-excel)
12. [Eliminacion masiva y limpieza](#12-eliminacion-masiva-y-limpieza)
13. [Arquitectura y acceso multiusuario](#13-arquitectura-y-acceso-multiusuario)
14. [Copia de seguridad y recuperacion](#14-copia-de-seguridad-y-recuperacion)
15. [Administracion del sistema](#15-administracion-del-sistema)
16. [Buenas practicas](#16-buenas-practicas)
17. [Preguntas frecuentes](#17-preguntas-frecuentes)

---

## 1. Introduccion

La aplicacion **Gestion de Muestras de Cafe Verde** permite registrar, consultar, catar, etiquetar, importar y controlar muestras de cafe verde dentro del flujo de trabajo de Indian Ecotrade.

Su objetivo principal es centralizar la informacion operativa de las muestras para que el equipo pueda:

- Saber que muestras existen y en que estado se encuentran.
- Localizar rapidamente una muestra por proveedor, referencia, CVC, origen, pais, calidad o estado.
- Registrar catas y conservar sus notas, puntuaciones y documentos.
- Generar etiquetas Avery con QR para identificar fisicamente cada muestra.
- Importar listados Excel de forma controlada, revisando duplicados antes de crear registros.
- Preparar vistas publicas de solo lectura mediante QR.
- Limpiar muestras de forma controlada cuando sea necesario reiniciar la base operativa.

### Flujo general de trabajo

El flujo recomendado es:

```text
Importar o crear muestra
↓
Revisar datos
↓
Aplicar importacion, si procede
↓
Imprimir etiqueta
↓
Pegar etiqueta fisica en la muestra
↓
Enviar o catar
↓
Registrar cata, fotos y documentos
↓
Actualizar estado
↓
Archivar cuando deje de gestionarse activamente
```

### Conceptos basicos

**Muestra**  
Registro principal de un cafe verde. Contiene datos como proveedor, referencia de proveedor, origen, calidad, CVC, contenedor, cantidades, estado y notas.

**Cata**  
Evaluacion sensorial y tecnica asociada a una muestra. Puede incluir cribas, humedad, defectos, puntuaciones, resultado, notas de cata, recomendaciones y fotos.

**Importacion**  
Proceso para subir un Excel, previsualizar sus filas, detectar duplicados y decidir que muestras crear. La aplicacion no crea muestras automaticamente al subir el archivo: primero genera una previsualizacion.

**Etiqueta**  
PDF imprimible en formato Avery L7108REV. Incluye datos principales de la muestra y un QR.

**QR**  
Codigo incluido en la etiqueta. Apunta a una ficha publica de solo lectura:

```text
/public/samples/{id}
```

**Envio**  
Registro de salida de una cantidad de muestra hacia un destino. Al registrar un envio, la cantidad disponible se reduce.

---

## 2. Acceso a la aplicacion

### URL local

Cuando la aplicacion se utiliza en el mismo ordenador donde se ejecuta Docker, se accede normalmente desde:

```text
http://localhost:8000
```

### URL en red

Para acceder desde otros portatiles o moviles de la misma red, se usa la IP del ordenador servidor:

```text
http://IP_DEL_PC_SERVIDOR:8000
```

Ejemplo:

```text
http://192.168.1.100:8000
```

La aplicacion esta preparada para escuchar en:

```text
0.0.0.0:8000
```

Esto permite que otros equipos de la red puedan acceder si el firewall y la red lo permiten.

### APP_BASE_URL

Para que los QR funcionen desde otros dispositivos, la variable `APP_BASE_URL` debe apuntar a una URL accesible desde esos dispositivos.

Ejemplo en oficina:

```text
APP_BASE_URL=http://192.168.1.100:8000
```

Ejemplo futuro con dominio:

```text
APP_BASE_URL=https://muestras.indianecotrade.es
```

### Navegacion principal

La barra superior incluye accesos a:

- **Dashboard**: resumen operativo.
- **Muestras**: listado, busqueda, filtros y acciones sobre muestras.
- **Etiquetas**: pantalla de impresion de etiquetas.
- **Importaciones**: subida y previsualizacion de Excel.
- **Nueva muestra**: creacion manual.
- **Comparador**: comparacion de muestras.

---

## 3. Dashboard

El Dashboard es la pantalla inicial de la aplicacion. Su objetivo es mostrar informacion operativa de un vistazo.

[CAPTURA DASHBOARD]

### KPIs

Los KPIs muestran conteos por estado y volumen operativo. Entre ellos:

- Total de muestras.
- Recibidas.
- Disponibles.
- Aprobadas.
- Rechazadas.
- Enviadas.
- Archivadas.

Estos indicadores ayudan a conocer rapidamente la situacion general del inventario de muestras.

### Ultimas muestras registradas

Muestra las muestras creadas mas recientemente. Es util para revisar si una importacion o alta manual ha quedado registrada.

### Muestras pendientes de catar

Lista muestras que aun no tienen catas asociadas. Sirve para priorizar trabajo del laboratorio o del equipo de calidad.

### Muestras sin stock

Muestra registros cuya cantidad disponible es cero o inferior. Estas muestras pueden estar enviadas, agotadas o necesitar revision.

### Ultimas catas realizadas

Permite consultar actividad reciente de evaluacion sensorial y tecnica.

---

## 4. Gestion de muestras

La gestion de muestras se realiza desde:

```text
/samples
```

Desde esta pantalla se puede:

- Buscar muestras.
- Filtrar por datos reales.
- Seleccionar varias muestras.
- Imprimir etiquetas.
- Eliminar seleccionadas.
- Abrir la ficha de una muestra.

### Crear muestra manualmente

La creacion manual se realiza desde:

```text
/samples/new
```

Tambien se accede desde el boton **Nueva muestra**.

#### Campos principales

**Codigo**  
Identificador interno de la muestra. Si se deja vacio, la aplicacion genera un codigo automaticamente.

Ejemplo:

```text
AUTO-20260619-AB12
```

**Fecha de recepcion**  
Fecha en la que se recibe o registra la muestra.

**Cantidad recibida (g)**  
Cantidad inicial recibida en gramos.

Ejemplo:

```text
500
```

**Cantidad disponible (g)**  
Cantidad que queda disponible para enviar, catar o gestionar. Si se deja vacia, se iguala a la cantidad recibida.

**Pais origen**  
Pais seleccionado desde la lista disponible en el formulario manual.

**Origen / region**  
Zona, pais, region, finca o denominacion de origen segun la informacion disponible.

Ejemplos:

```text
Uganda
Sierra Leona
Costa de Marfil
Huila
Cerrado
```

**Proveedor**  
Empresa o persona que suministra la muestra. Es un campo obligatorio en la creacion manual.

**Referencia proveedor**  
Referencia comercial del proveedor. Es obligatoria en la creacion manual y muy importante para identificar muestras.

**Numero muestra proveedor**  
Numero adicional asignado por el proveedor, si existe.

**Numero de Contenedor**  
Campo para registrar el contenedor asociado a la muestra.

Ejemplo:

```text
MSCU1234567
```

**Ubicacion fisica**  
Ubicacion interna donde se encuentra la muestra, si se utiliza.

**Variedad**  
Variedad botanica o descripcion del cafe.

**Cosecha**  
Periodo o fecha de cosecha.

**Altitud**  
Altitud en metros sobre el nivel del mar, si aplica.

**Metodo de procesamiento**  
Proceso del cafe, por ejemplo lavado, natural, honey, anaerobico o fermentado.

**Calidad**  
Descripcion comercial o tecnica de la calidad. Es obligatoria en la creacion manual.

Ejemplos:

```text
Robusta 1
Organic FAQ
Descafeinado 18
Conillon 16
```

**Almacen**  
Almacen o ubicacion logistica.

**Tipo de muestra**  
Tipo interno de muestra, si se utiliza.

**Categoria**  
Categoria comercial o tecnica.

**Contrato CVC**  
Contrato de compra CVC, si existe. Este dato aparece en la etiqueta cuando esta informado.

**Contrato CVV**  
Contrato de venta CVV, si existe.

**Resultado comercial**  
Resultado o clasificacion comercial.

**Notas / observaciones**  
Texto libre para registrar comentarios importantes.

### Editar muestra

Desde la ficha de muestra, pulsar **Editar muestra**.

La edicion permite actualizar los mismos datos principales del registro.

### Consultar muestra

Desde `/samples`, pulsar sobre el codigo de la muestra o el boton **Detalle**.

La ficha de muestra muestra:

- Cabecera con codigo, origen, pais, proveedor y estado.
- Cantidades.
- Datos generales.
- Datos fisicos y tecnicos.
- Catas.
- Documentos y fotografias.
- Envios.
- Historial de actividad, si existe.

### Eliminar muestra

Desde la ficha de muestra existe el boton **Eliminar muestra**.

La eliminacion borra:

- La muestra.
- Sus catas.
- Sus documentos y fotos asociados.
- Sus envios.
- Sus eventos.

Antes de borrar, la aplicacion solicita confirmacion.

---

## 5. Estados de muestra

Los estados validos son:

### Recibida

La muestra ha sido registrada o importada, pero aun no se ha clasificado como disponible o evaluada.

Usar cuando:

- Llega una muestra nueva.
- Todavia no se ha revisado.
- Aun no se ha catado.

### Disponible

La muestra tiene stock utilizable.

Usar cuando:

- Hay cantidad disponible.
- Puede enviarse, catarse o gestionarse.

### Aprobada

La muestra ha sido evaluada positivamente.

Usar cuando:

- La cata o revision comercial ha sido favorable.
- Puede considerarse apta para avanzar.

### Rechazada

La muestra no cumple los criterios esperados.

Usar cuando:

- La cata no es aceptable.
- La calidad no corresponde.
- No interesa continuar con la muestra.

### Enviada

La muestra ha sido enviada o ya no tiene cantidad disponible por envios.

Usar cuando:

- Se ha registrado un envio.
- La cantidad disponible queda en cero.

### Archivada

La muestra ya no se gestiona activamente.

Usar cuando:

- Se conserva solo como historico.
- Ya no requiere acciones operativas.

---

## 6. Busqueda y filtros

La pantalla `/samples` incluye filtros para localizar muestras rapidamente.

### Filtro por codigo

Permite buscar por codigo interno.

Ejemplo:

```text
IMP-11
```

### Filtro por CVC

Permite buscar por contrato CVC.

Ejemplo:

```text
69-2025CVC
```

### Filtro por pais

El filtro de pais se genera dinamicamente desde las muestras existentes.

Puede incluir valores como:

- Sierra Leona
- Costa de Marfil
- Uganda
- Vietnam
- Brasil

Si una muestra no tiene pais separado pero su origen contiene un pais reconocible, la aplicacion puede usar ese origen como pais visible.

### Filtro por origen

El filtro de origen tambien se genera desde datos reales.

Sirve para filtrar por origen, region o denominacion registrada en las muestras.

### Filtro por proveedor

El desplegable se alimenta de proveedores existentes en Samples.

Ejemplo:

```text
TORESA
Bijdendijk
Sucden
Phuc Sinh
```

### Filtro por referencia proveedor

Permite buscar por referencia del proveedor.

### Filtro por calidad

El desplegable se alimenta de calidades reales registradas.

Ejemplos:

```text
Robusta 1
Organic FAQ
Descafeinado 18
Conillon 16
```

### Filtro por estado

Mantiene la lista fija de estados validos:

- Recibida
- Disponible
- Aprobada
- Rechazada
- Enviada
- Archivada

### Filtros dinamicos

Los filtros de Pais, Proveedor, Calidad y Origen se generan desde los datos reales.

La aplicacion evita mostrar:

- `None`
- `null`
- `nan`
- `-`
- valores vacios

Tambien reduce duplicados por diferencias de mayusculas, minusculas, tildes y espacios.

---

## 7. Gestion de catas

Las catas se gestionan desde la ficha de una muestra.

[CAPTURA CATA]

### Crear cata

En la ficha de muestra, abrir la seccion **Catas** y pulsar **Crear cata**.

Campos principales:

**Fecha de cata**  
Fecha en la que se realiza la evaluacion.

**Fecha de tueste**  
Fecha del tueste de la muestra, si aplica.

**Evaluador**  
Persona que realiza la cata. Es obligatorio.

**Analisis de criba**  
Permite registrar porcentajes de:

- Criba 18+
- Criba 17
- Criba 16+
- Criba 15
- Criba 14+
- Criba 13
- Criba 12
- Criba plato

**Humedad**  
Porcentaje de humedad.

**Defectos primarios y secundarios**  
Numero de defectos detectados.

**Valoracion**  
Valor numerico de 0 a 100.

**Resultado**  
Puede ser:

- Pendiente
- Aprobada
- Rechazada

**Puntuaciones de cata**  
Valores de 0 a 10 para:

- Aroma
- Acidez
- Cuerpo
- Sabor
- Post-gusto
- Limpieza
- Balance

**Notas de cata**  
Descripcion sensorial y observaciones.

**Recomendaciones**  
Comentarios tecnicos o comerciales.

### Ver catas

Las catas registradas aparecen en la seccion **Catas** de la ficha.

Cada cata muestra:

- Fecha.
- Evaluador.
- Resultado.
- Puntuaciones.
- Datos fisicos.
- Notas.
- Documentos o fotos asociados.

### PDF de cata

Cada cata puede generar una **Ficha de cata PDF** desde su boton correspondiente.

El PDF incluye:

- Cabecera corporativa.
- Datos de muestra.
- Datos fisicos.
- Datos sensoriales.
- Notas de cata.
- Fotografias si existen.

---

## 8. Fotografias y documentos

La ficha de muestra incluye una seccion de documentos y fotografias.

### Subir documentos o fotos de muestra

En la seccion **Documentos y fotografias**, seleccionar un archivo y especificar un tipo.

Ejemplos de tipo:

```text
cafe_verde
certificado
analisis
```

### Subir documentos o fotos de cata

Dentro de cada cata tambien se pueden subir fotos o documentos asociados a esa cata.

Ejemplos:

```text
cafe_verde
cafe_tostado
molido
ficha
```

### Consultar documentos

Los documentos aparecen como tarjetas en la ficha.

Si son imagenes, se muestran como miniaturas.

### Eliminar documentos

Actualmente la eliminacion individual de documentos no aparece como accion separada en la interfaz. Los documentos asociados se eliminan cuando se elimina la muestra o cuando se realiza una limpieza administrativa de muestras.

---

## 9. Etiquetas

La aplicacion genera etiquetas en PDF para imprimir y pegar en las muestras fisicas.

[CAPTURA ETIQUETAS]

### Etiquetas Avery L7108REV

El modelo soportado es:

```text
Avery L7108REV
```

Caracteristicas:

- Hoja A4 vertical.
- Matriz 3 x 3.
- 9 etiquetas por hoja.
- Celda fisica 62 x 89 mm.
- Diseno interno horizontal 89 x 62 mm rotado.

### Seleccion multiple

Desde `/samples`, marcar varias muestras con los checkboxes y pulsar **Imprimir etiqueta**.

La aplicacion abre la pantalla de etiquetas con esas muestras preseleccionadas.

### Pantalla de etiquetas

Desde `/labels` se puede:

- Seleccionar muestras manualmente.
- Elegir modelo Avery.
- Indicar numero de copias.
- Indicar posicion inicial de impresion entre 1 y 9.

La posicion inicial sirve para reutilizar hojas parcialmente usadas.

Ejemplo:

Si ya se usaron las tres primeras etiquetas de la hoja, elegir posicion inicial:

```text
4
```

### Diseno de etiqueta

La etiqueta incluye:

- Cabecera con pais/origen.
- Colores de bandera por pais.
- Indian Ecotrade.
- Calidad.
- Proveedor.
- Referencia proveedor.
- CVC, si existe.
- QR grande a la derecha.

No incluye:

- Codigo interno.
- Sacos/B.B.
- Ubicacion.
- Cantidades disponibles.

### Colores especiales por calidad

La linea **Calidad** se resalta segun el texto.

Si contiene conceptos ecologicos:

- Ecológico
- ECO
- Orgánico
- Organic
- Bio

Se muestra con fondo verde suave.

Si contiene conceptos descafeinados:

- Descafeinado
- Decaf
- Decaff
- Decaffeinated
- Desca

Se muestra con fondo marron claro o naranja suave.

Si contiene ambos conceptos, se prioriza el estilo descafeinado y se muestra un indicador ECO cuando cabe.

---

## 10. QR publicos

Los QR de las etiquetas apuntan a una ficha publica de solo lectura:

[CAPTURA QR]

```text
/public/samples/{id}
```

Ejemplo:

```text
http://192.168.1.100:8000/public/samples/25
```

La ficha publica muestra informacion real y relevante:

- Codigo o referencia.
- Pais/origen.
- Proveedor.
- Referencia proveedor.
- CVC.
- Calidad.
- Estado.
- Notas basicas si existen.
- Ultima cata si existe.
- Fotografias y documentos accesibles si existen.

La ficha publica no permite:

- Editar.
- Borrar.
- Registrar catas.
- Registrar envios.
- Subir documentos.

En el futuro se puede sustituir el identificador numerico por un token publico.

---

## 11. Importacion Excel

La importacion Excel permite cargar listados de muestras de forma controlada.

[CAPTURA IMPORTACIONES]

Ruta:

```text
/imports
```

### Crear importacion

1. Ir a **Importaciones**.
2. Seleccionar archivo Excel.
3. Pulsar **Previsualizar**.

La aplicacion procesa las pestañas configuradas para importacion:

- Robusta America.
- Robusta Africa.
- Robusta Asia.
- Descafeinados.

Ignora pestañas no previstas para importacion, como historicos de envios.

### Previsualizacion

Tras subir el Excel, la aplicacion crea un batch de importacion y muestra una previsualizacion.

La previsualizacion permite revisar:

- Total de filas.
- Nuevas.
- Existentes.
- Duplicadas.
- Incompletas.
- Errores.
- Avisos.

### Estados de filas de importacion

**CREATE_CANDIDATE**  
Fila candidata a crear una muestra nueva.

**DUPLICATE_IN_FILE**  
Fila duplicada dentro del propio Excel.

**EXISTING_MATCH**  
Fila que coincide con una muestra existente.

**INCOMPLETE**  
Fila incompleta. Por ejemplo, sin referencia proveedor.

**WARNING_SIMILAR**  
Fila con aviso de similitud. No se aplica automaticamente.

**ERROR**  
Fila con error que impide procesarla.

### Seleccion manual

En la previsualizacion se pueden seleccionar manualmente las filas `CREATE_CANDIDATE` que se quieren aplicar.

Por defecto:

- `CREATE_CANDIDATE` aparece seleccionada.
- Duplicadas, existentes, incompletas y errores quedan bloqueadas.

Controles disponibles:

- Seleccionar todas las CREATE_CANDIDATE.
- Seleccionar visibles filtradas.
- Deseleccionar todas.
- Excluir seleccionadas.

### Aplicar importacion

Pulsar **Aplicar filas seleccionadas**.

La aplicacion solicita confirmacion:

```text
Se crearan X muestras. Las no seleccionadas quedaran excluidas. ¿Continuar?
```

Al aplicar:

- Se crean muestras solo para filas seleccionadas.
- No se crean duplicadas.
- No se actualizan existentes.
- No se aplican incompletas ni errores.
- Cada fila creada queda vinculada a su `sample_id`.

### Impresion de etiquetas tras importacion

Cuando un batch crea muestras, aparece un enlace para imprimir etiquetas de las muestras creadas:

```text
/labels?ids=...
```

Esto permite etiquetar rapidamente todas las muestras recien importadas.

---

## 12. Eliminacion masiva y limpieza

### Eliminar seleccionadas

Desde `/samples`, marcar varias muestras y pulsar **Eliminar seleccionadas**.

La aplicacion muestra confirmacion con:

- Numero de muestras seleccionadas.
- Aviso de borrado irreversible.

Esta accion elimina:

- Muestras.
- Catas.
- Documentos/fotos.
- Envios.
- Eventos.

### Limpiar todas las muestras

La opcion administrativa esta en:

```text
Importaciones -> Administracion / Limpiar muestras
```

Ruta:

```text
/admin/clean-samples
```

Para ejecutar la limpieza hay que escribir exactamente:

```text
BORRAR MUESTRAS
```

Esta accion borra todas las muestras y datos asociados, pero conserva:

- ImportBatch.
- ImportRow.
- Datos raw/normalized de importacion.
- Excels originales importados.
- Configuracion.
- Logo.
- Estructura de base de datos.

Las filas de importacion vinculadas a muestras se desvinculan:

```text
sample_id = NULL
final_action = CLEANED_SAMPLE
status = CLEANED_SAMPLE
```

Usar esta opcion solo cuando se quiera empezar de cero con las muestras.

---

## 13. Arquitectura y acceso multiusuario

La aplicacion esta preparada para funcionar como una herramienta compartida por varios portatiles dentro de la misma red local, siempre que exista un ordenador servidor ejecutando Docker.

### Servidor central

El modelo recomendado es:

```text
Un ordenador servidor
  -> ejecuta Docker
  -> contiene la base de datos SQLite
  -> contiene la carpeta uploads
  -> publica la aplicacion en el puerto 8000

Otros portatiles
  -> acceden por navegador
  -> no necesitan tener la base de datos localmente
  -> no guardan archivos de la aplicacion
```

Esto evita que cada usuario tenga una copia distinta de la informacion. La aplicacion debe usarse desde una unica instancia central cuando trabaje mas de una persona.

### Acceso desde otros portatiles

Para acceder desde otro equipo de la misma red:

1. Arrancar la aplicacion en el ordenador servidor.
2. Identificar la IP local del servidor.
3. Abrir en el otro portatil:

```text
http://IP_DEL_PC_SERVIDOR:8000
```

Ejemplo:

```text
http://192.168.1.100:8000
```

El servicio Docker debe publicar el puerto `8000` y escuchar en `0.0.0.0:8000`, no solo en `localhost`.

### APP_BASE_URL

`APP_BASE_URL` define la URL publica que la aplicacion usa para construir enlaces QR.

En un uso local de oficina:

```text
APP_BASE_URL=http://192.168.1.100:8000
```

En un dominio futuro:

```text
APP_BASE_URL=https://muestras.indianecotrade.es
```

Si `APP_BASE_URL` esta configurado como `http://localhost:8000`, los QR funcionaran en el propio servidor, pero no desde moviles u otros portatiles. Para etiquetas fisicas, conviene usar siempre una URL accesible por quien vaya a escanearlas.

### Funcionamiento de los QR

Cada QR apunta a:

```text
{APP_BASE_URL}/public/samples/{sample_id}
```

La ruta publica muestra una ficha de solo lectura. No permite editar, borrar, aplicar importaciones ni cambiar estados.

Mas adelante se puede reforzar el acceso sustituyendo el identificador numerico por un token publico. La version actual ya separa la vista publica de las pantallas de gestion.

---

## 14. Copia de seguridad y recuperacion

La informacion principal de la aplicacion se reparte entre la base de datos SQLite y los archivos subidos. Para una copia de seguridad util hay que conservar ambas partes.

### Base de datos SQLite

La base de datos contiene:

- Muestras.
- Catas.
- Envios.
- Eventos.
- Importaciones.
- Filas de importacion.
- Relaciones entre muestras y documentos.

En la configuracion habitual, la ruta se define mediante `DATABASE_URL`. Un ejemplo frecuente es:

```text
sqlite:///./data/muestras.db
```

Para hacer backup, copiar el archivo `.db` correspondiente cuando la aplicacion no este escribiendo datos o despues de detener Docker.

### Carpeta uploads

La carpeta `uploads` contiene documentos, fotos y Excels originales importados. Su ruta se define con:

```text
UPLOADS_DIR=./uploads
```

Esta carpeta debe estar en un volumen persistente de Docker. Si se copia solo la base de datos y no `uploads`, las fichas podran conservar referencias a archivos que ya no existen.

### Excel importados

Los Excels originales de importacion se guardan dentro de `UPLOADS_DIR/imports/{batch_id}/`. Conviene conservarlos porque permiten auditar de donde salieron las filas de una importacion.

### Que copiar para un backup completo

Como minimo:

- Archivo SQLite, por ejemplo `data/muestras.db`.
- Carpeta `uploads/` completa.
- Archivo `.env` o configuracion equivalente.
- Version del codigo desplegado.

Recomendacion operativa:

1. Detener la aplicacion.
2. Copiar `data/`.
3. Copiar `uploads/`.
4. Guardar la copia con fecha.
5. Arrancar de nuevo la aplicacion.

### Recuperacion

Para recuperar:

1. Detener Docker.
2. Restaurar el archivo SQLite en la ruta esperada.
3. Restaurar la carpeta `uploads`.
4. Revisar `.env`.
5. Arrancar la aplicacion.
6. Abrir `/samples`, `/imports` y una ficha con documentos para comprobar que la informacion aparece.

---

## 15. Administracion del sistema

Las acciones administrativas permiten corregir o limpiar datos de forma controlada. Deben usarse con prudencia, especialmente cuando hay muestras reales en gestion.

### Limpieza de muestras

La pantalla:

```text
/admin/clean-samples
```

permite borrar todas las muestras y sus datos asociados. Requiere escribir exactamente:

```text
BORRAR MUESTRAS
```

Esta medida evita ejecuciones accidentales. Es util cuando se quiere reiniciar la base operativa despues de pruebas o antes de una carga inicial definitiva.

La limpieza conserva el historico de importaciones y los Excels originales, pero desvincula las filas de importacion de las muestras eliminadas.

### Rollback simple de importaciones

La pantalla de detalle de una importacion puede mostrar la accion **Eliminar muestras creadas por esta importacion** si el batch tiene muestras asociadas.

Esta accion:

- Borra solo muestras creadas por ese batch.
- No borra muestras externas.
- Limpia el `sample_id` de las filas de importacion.
- Marca las filas como eliminadas por rollback simple.
- Mantiene el historico del batch.

Es una herramienta util cuando se aplica una importacion de prueba y se quiere deshacer sin tocar otras muestras.

### Eliminacion masiva

Desde `/samples` se pueden seleccionar varias muestras y usar **Eliminar seleccionadas**.

Debe utilizarse cuando se quieren borrar registros concretos, no toda la base. La aplicacion elimina las relaciones dependientes de esas muestras: catas, documentos/fotos, envios y eventos asociados.

### Recomendaciones administrativas

- Hacer copia de seguridad antes de limpiezas generales.
- Revisar los filtros antes de seleccionar muestras para borrado masivo.
- Usar rollback de importacion cuando el problema procede de un batch concreto.
- Usar limpieza total solo para reinicios controlados.
- No borrar carpetas de `uploads` manualmente si hay muestras activas que puedan referenciar esos archivos.

---

## 16. Buenas practicas

### Flujo recomendado

```text
Importar
↓
Revisar
↓
Aplicar
↓
Etiquetar
↓
Enviar
↓
Catar
↓
Archivar
```

### Recomendaciones

- Revisar siempre la previsualizacion antes de aplicar una importacion.
- No aplicar duplicados salvo que se haya comprobado que son muestras distintas.
- Mantener informada la referencia proveedor.
- Completar CVC cuando exista.
- Usar contenedor cuando ayude a diferenciar muestras similares.
- Imprimir etiquetas justo despues de crear o importar muestras.
- Pegar la etiqueta fisica antes de mover o enviar la muestra.
- Subir fotos de cafe verde y tostado cuando haya cata.
- Registrar notas de cata claras y utiles.
- Usar Archivada para muestras que ya no se gestionan activamente.
- Configurar `APP_BASE_URL` con una URL accesible desde otros portatiles para que los QR funcionen.

---

## 17. Preguntas frecuentes

### 1. ¿Puedo usar la aplicacion desde otro portatil?

Si. El ordenador servidor debe estar encendido, Docker debe estar ejecutando la aplicacion y debes acceder a:

```text
http://IP_DEL_PC_SERVIDOR:8000
```

### 2. ¿Por que el QR abre localhost y no funciona desde el movil?

Porque `APP_BASE_URL` esta configurado como `localhost`. Debe configurarse con una URL accesible desde el movil, por ejemplo:

```text
http://192.168.1.100:8000
```

### 3. ¿Que muestra el QR?

Abre una ficha publica de solo lectura con datos principales de la muestra, ultima cata y documentos/fotos si existen.

### 4. ¿Se puede editar desde la ficha publica?

No. La ficha publica es solo lectura.

### 5. ¿Puedo crear muestras una a una?

Si. Usar **Nueva muestra** y completar el formulario manual.

### 6. ¿Que pasa si dejo el codigo vacio?

La aplicacion genera un codigo automatico.

### 7. ¿Que campos son obligatorios al crear muestra manual?

En la interfaz manual son obligatorios Proveedor, Referencia proveedor y Calidad.

### 8. ¿Puedo importar un Excel directamente sin revisar?

No. Primero se crea una previsualizacion. Luego se decide que filas aplicar.

### 9. ¿Que significa CREATE_CANDIDATE?

Es una fila que la aplicacion considera candidata para crear una nueva muestra.

### 10. ¿Que significa DUPLICATE_IN_FILE?

Es una fila duplicada dentro del Excel. No se aplica automaticamente.

### 11. ¿Que significa EXISTING_MATCH?

La fila coincide con una muestra existente. En esta fase no se actualizan muestras existentes automaticamente.

### 12. ¿Puedo imprimir etiquetas de varias muestras?

Si. En `/samples`, seleccionar varias muestras y pulsar **Imprimir etiqueta**.

### 13. ¿Puedo empezar a imprimir en la posicion 4 de una hoja Avery?

Si. En `/labels`, elegir posicion inicial 4.

### 14. ¿Por que algunas etiquetas tienen cabecera con colores distintos?

La cabecera usa colores de bandera segun pais/origen reconocido.

### 15. ¿Por que la calidad aparece con fondo verde?

Porque contiene un termino ecologico, organico, organic, bio o ECO.

### 16. ¿Por que la calidad aparece con fondo marron/naranja?

Porque contiene un termino relacionado con descafeinado, como Descafeinado o Decaf.

### 17. ¿Puedo subir fotos a una cata?

Si. Dentro de cada cata hay opcion para subir documentos o fotografias.

### 18. ¿Puedo generar PDF de cata?

Si. Cada cata registrada tiene un boton para generar ficha de cata PDF.

### 19. ¿Que pasa al registrar un envio?

Se crea un envio y se reduce la cantidad disponible de la muestra.

### 20. ¿Cuando uso Archivada?

Cuando la muestra ya no se gestiona activamente y se conserva solo como historico.

### 21. ¿Puedo borrar varias muestras a la vez?

Si. En `/samples`, seleccionar varias muestras y pulsar **Eliminar seleccionadas**.

### 22. ¿La limpieza administrativa borra las importaciones?

No. Conserva batches, filas de importacion y archivos Excel originales.

### 23. ¿La limpieza administrativa borra las fotos?

Borra documentos/fotos asociados a muestras. No borra los Excel originales de importacion.

### 24. ¿Puedo recuperar muestras despues de borrarlas?

No desde la interfaz. El borrado se considera irreversible. Por eso se pide confirmacion.

### 25. ¿Por que no veo una muestra en el filtro de pais?

El filtro se genera con valores reales de las muestras. Si no aparece, revisar si el pais/origen esta informado de forma reconocible.

### 26. ¿Que hago si hay duplicados en una importacion?

Revisar el grupo duplicado. Si son duplicados reales, no aplicarlos. Si son muestras distintas, comprobar CVC, referencia y contenedor antes de decidir.

### 27. ¿Puedo actualizar muestras existentes desde una importacion?

Actualmente no se aplica update masivo. Las filas existentes se identifican, pero no se actualizan automaticamente.

### 28. ¿Donde se guardan documentos y fotos?

En el directorio persistente de uploads configurado para la aplicacion.

### 29. ¿La aplicacion esta preparada para PostgreSQL?

La aplicacion esta organizada con SQLAlchemy y variables de entorno de base de datos, lo que facilita una futura migracion. Actualmente se usa SQLite.

### 30. ¿Como se recomienda trabajar cada dia?

Entrar al Dashboard, revisar pendientes, importar o crear nuevas muestras, imprimir etiquetas, registrar catas/envios y mantener los estados actualizados.
