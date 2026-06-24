# Guia de Usuario

## Indice

- [Introduccion](#introduccion)
- [Acceso al sistema](#acceso-al-sistema)
- [Dashboard](#dashboard)
- [Crear muestra](#crear-muestra)
- [Editar muestra](#editar-muestra)
- [Estados](#estados)
- [Fotografias](#fotografias)
- [Documentos](#documentos)
- [Catas](#catas)
- [Comparador](#comparador)
- [Etiquetas](#etiquetas)
- [QR publico](#qr-publico)
- [Importacion Excel](#importacion-excel)
- [Eliminacion de muestras](#eliminacion-de-muestras)
- [Resolucion de problemas frecuentes](#resolucion-de-problemas-frecuentes)

## Introduccion

Gestion de Muestras Cafe Verde es una aplicacion interna para controlar muestras comerciales de cafe verde. Permite registrar muestras, consultar su informacion, mantener stock, crear catas, adjuntar fotos/documentos, imprimir etiquetas y preparar importaciones Excel con revision previa.

Flujo recomendado:

```text
Importar o crear muestra
Revisar datos
Aplicar/importar si procede
Etiquetar
Enviar
Catar
Actualizar estado
Archivar cuando deje de estar activa
```

[CAPTURA_PENDIENTE]

## Acceso al sistema

Acceso local en el servidor:

```text
http://localhost:8000
```

Acceso desde otro equipo de la red:

```text
http://192.168.1.37:8000
```

La navegacion principal incluye dashboard, muestras, comparador, etiquetas e importaciones.

## Dashboard

El dashboard resume la situacion operativa:

- Total de muestras.
- Muestras recibidas.
- Muestras disponibles.
- Muestras aprobadas.
- Muestras rechazadas.
- Muestras enviadas.
- Muestras archivadas.
- Stock disponible en gramos.
- Muestras pendientes de catar.
- Muestras sin stock.
- Ultimas muestras registradas.
- Ultimas catas realizadas.
- Muestras por origen, usando el pais cuando no existe region/zona.

[CAPTURA_PENDIENTE]

## Crear muestra

Desde `Nueva muestra` se puede registrar una muestra manualmente.

Campos principales:

- Codigo de muestra: puede dejarse vacio para generacion automatica.
- Fecha de recepcion.
- Cantidad recibida en gramos.
- Cantidad disponible en gramos.
- Pais origen.
- Estado.
- Region/origen.
- Productor o proveedor.
- Referencia proveedor.
- Numero de muestra proveedor.
- Numero de contenedor.
- Ubicacion fisica.
- Variedad o tipo.
- Cosecha.
- Altitud.
- Metodo de procesamiento.
- Calidad.
- Almacen.
- Tipo de muestra.
- Categoria.
- Contrato CVC.
- Cantidad contrato.
- Resultado comercial.
- Observaciones.

## Editar muestra

En la ficha de muestra se usa `Editar muestra`. La pantalla permite modificar datos comerciales, origen, cantidades, estado, CVC, contenedor, almacen, notas y datos tecnicos.

El campo Estado es un selector cerrado para evitar valores no validos.

## Estados

Estados permitidos:

- Recibida: muestra registrada, pendiente de gestion inicial o cata.
- Disponible: muestra con stock utilizable.
- Enviada: muestra enviada o sin stock por envio.
- Aprobada: muestra aprobada comercialmente o por cata.
- Rechazada: muestra no valida o descartada.
- Archivada: muestra que ya no se gestiona activamente.

Los badges de estado aparecen en dashboard, listado, ficha y QR publico.

## Fotografias

En la ficha de muestra se pueden subir fotografias como documentos. Las fotos se muestran en la ficha publica QR y en PDFs cuando son imagenes accesibles.

Recomendacion de nombres:

- `cafe_verde...`
- `cafe_tostado...`

Esto ayuda a priorizar el orden visual.

[CAPTURA_PENDIENTE]

## Documentos

La ficha de muestra permite adjuntar documentos o fotografias. Los documentos quedan asociados a la muestra y se listan en la ficha.

## Catas

Cada muestra puede tener catas. Una cata incluye:

- Evaluador.
- Fecha de cata.
- Fecha de tueste.
- Cribas.
- Humedad.
- Defectos.
- Aroma.
- Acidez.
- Cuerpo.
- Sabor.
- Regusto.
- Limpieza.
- Balance.
- Puntuaciones.
- Resultado.
- Notas de cata.
- Recomendaciones.

Desde la ficha se puede generar el PDF de cata.

[CAPTURA_PENDIENTE]

## Comparador

El comparador permite elegir varias muestras y verlas lado a lado. La identificacion principal usa calidad, pais, tipo, proveedor, CVC y referencia proveedor. El codigo interno queda como dato secundario.

Campos comparados:

- Calidad.
- Tipo.
- Pais.
- Origen/zona.
- Proveedor.
- Referencia proveedor.
- CVC.
- Contenedor.
- Almacen.
- Cantidad disponible.
- Productor.
- Altitud.
- Proceso.
- Cosecha.
- Puntuaciones de cata si existen.

## Etiquetas

La aplicacion genera etiquetas Avery L7108REV.

Flujo:

1. Seleccionar muestras.
2. Ir a etiquetas.
3. Elegir modelo L7108REV.
4. Indicar posicion inicial de 1 a 9.
5. Indicar numero de copias.
6. Generar PDF.

La etiqueta incluye identidad del cafe, pais/origen, colores de bandera, calidad, tipo, referencia proveedor, CVC si existe y QR publico.

[CAPTURA_PENDIENTE]

## QR publico

Cada etiqueta contiene un QR que apunta a:

```text
/public/samples/{id}
```

La vista publica es de solo lectura. Muestra informacion comercial, estado, cata reciente, fotos y documentos accesibles.

[CAPTURA_PENDIENTE]

## Importacion Excel

La importacion Excel funciona con staging y previsualizacion.

Pasos:

1. Entrar en Importaciones.
2. Subir Excel.
3. Revisar previsualizacion.
4. Ver filas candidatas, duplicadas, existentes, incompletas o con error.
5. Seleccionar filas a aplicar.
6. Aplicar solo las filas seleccionadas.
7. Imprimir etiquetas de muestras creadas si procede.

Estados de fila:

- CREATE_CANDIDATE.
- DUPLICATE_IN_FILE.
- EXISTING_MATCH.
- INCOMPLETE.
- WARNING_SIMILAR.
- ERROR.

[CAPTURA_PENDIENTE]

## Eliminacion de muestras

Opciones disponibles:

- Eliminar una muestra desde su ficha.
- Eliminar varias muestras seleccionadas desde el listado.
- Eliminar muestras creadas por un batch de importacion.
- Limpiar todas las muestras desde administracion.

La limpieza administrativa requiere confirmacion textual exacta:

```text
BORRAR MUESTRAS
```

## Resolucion de problemas frecuentes

**No veo una muestra despues de importar.**  
Revise si la fila estaba seleccionada y si su estado era `CREATE_CANDIDATE`.

**Aparece como duplicada.**  
La aplicacion compara proveedor, referencia proveedor, CVC y contenedor.

**El QR no abre la muestra correcta.**  
Revise `APP_BASE_URL` y confirme que el servidor es accesible desde el movil.

**El dashboard no cambia.**  
Actualice la pagina. Las metricas se recalculan desde base de datos en cada carga.

**No puedo cambiar un estado.**  
Use el selector de estado en editar muestra; no se admiten estados escritos manualmente fuera de la lista.

**La etiqueta empieza en una posicion incorrecta.**  
Use posicion inicial 1 a 9 segun la hoja Avery disponible.

**Una muestra aparece sin foto.**  
Confirme que el archivo se subio como imagen y que sigue en la carpeta `uploads`.

**Necesito empezar de cero.**  
Use Administracion / Limpiar muestras, con extrema precaucion.
