# Checklist de puesta en marcha

## Gestion de Muestras de Cafe Verde - Indian Ecotrade

Este checklist sirve para preparar una instalacion local o de oficina antes de empezar a usar la aplicacion con datos reales.

---

## 1. Preparacion del equipo servidor

- [ ] Elegir el ordenador que actuara como servidor central.
- [ ] Confirmar que el equipo permanecera encendido mientras otros usuarios necesiten acceder.
- [ ] Instalar Docker Desktop.
- [ ] Comprobar que Docker arranca correctamente.
- [ ] Descargar o clonar el repositorio de la aplicacion.
- [ ] Confirmar que existe el archivo `docker-compose.yml`.
- [ ] Confirmar que existen las carpetas persistentes necesarias, por ejemplo `data/` y `uploads/`.

---

## 2. Configuracion del archivo .env

- [ ] Crear `.env` a partir de `.env.example`.
- [ ] Revisar `DATABASE_URL`.
- [ ] Revisar `UPLOADS_DIR`.
- [ ] Configurar `APP_BASE_URL`.

Ejemplo para uso en el propio servidor:

```text
APP_BASE_URL=http://localhost:8000
```

Ejemplo recomendado para red local:

```text
APP_BASE_URL=http://192.168.1.100:8000
```

- [ ] Confirmar que `APP_BASE_URL` no apunta a `localhost` si se van a escanear QR desde moviles u otros portatiles.
- [ ] Guardar una copia segura del `.env`.

---

## 3. Arranque con Docker

- [ ] Abrir terminal en la carpeta del proyecto.
- [ ] Ejecutar:

```bash
docker compose up --build
```

- [ ] Confirmar que la aplicacion queda disponible en el puerto `8000`.
- [ ] Confirmar que no aparecen errores de base de datos.
- [ ] Confirmar que se crean o usan correctamente los directorios persistentes.

---

## 4. Comprobacion local

Abrir desde el equipo servidor:

```text
http://localhost:8000
```

Comprobar:

- [ ] Carga el Dashboard.
- [ ] Carga `/samples`.
- [ ] Carga `/samples/new`.
- [ ] Carga `/imports`.
- [ ] Carga `/labels`.
- [ ] Carga `/compare`.

---

## 5. Comprobacion de red

- [ ] Obtener la IP local del ordenador servidor.
- [ ] Abrir desde otro portatil:

```text
http://IP_DEL_PC_SERVIDOR:8000
```

Ejemplo:

```text
http://192.168.1.100:8000
```

Comprobar:

- [ ] El Dashboard carga desde otro equipo.
- [ ] El listado de muestras carga desde otro equipo.
- [ ] La pantalla de etiquetas carga desde otro equipo.
- [ ] La pantalla de importaciones carga desde otro equipo.
- [ ] El firewall del servidor no bloquea el puerto `8000`.

---

## 6. Prueba de QR

- [ ] Crear una muestra de prueba o usar una muestra existente.
- [ ] Generar una etiqueta Avery.
- [ ] Confirmar que el QR apunta a:

```text
{APP_BASE_URL}/public/samples/{sample_id}
```

- [ ] Escanear el QR desde un movil conectado a la misma red.
- [ ] Confirmar que abre la ficha publica.
- [ ] Confirmar que la ficha publica es de solo lectura.
- [ ] Confirmar que muestra datos reales de la muestra.

Si el QR abre `localhost`, revisar `APP_BASE_URL`.

---

## 7. Importacion inicial

- [ ] Ir a **Importaciones**.
- [ ] Subir el Excel inicial.
- [ ] Revisar que se procesan solo las pestanas previstas.
- [ ] Revisar el resumen:
  - [ ] Total filas.
  - [ ] Nuevas.
  - [ ] Existentes.
  - [ ] Duplicadas.
  - [ ] Incompletas.
  - [ ] Errores.
- [ ] Revisar filas `DUPLICATE_IN_FILE`.
- [ ] Revisar filas `EXISTING_MATCH`.
- [ ] Revisar filas `INCOMPLETE`.
- [ ] Confirmar que solo estan seleccionadas las filas `CREATE_CANDIDATE`.
- [ ] Aplicar solo cuando la previsualizacion sea correcta.
- [ ] Confirmar que se crean las muestras esperadas.
- [ ] Generar etiquetas de las muestras creadas.

---

## 8. Validacion despues de importar

- [ ] Abrir `/samples`.
- [ ] Filtrar por pais.
- [ ] Filtrar por proveedor.
- [ ] Filtrar por calidad.
- [ ] Filtrar por CVC.
- [ ] Abrir varias fichas de muestra.
- [ ] Confirmar que el estado inicial es correcto.
- [ ] Confirmar que las etiquetas se generan.
- [ ] Confirmar que el enlace de QR publico funciona.

---

## 9. Copia de seguridad inicial

Antes de empezar trabajo real:

- [ ] Detener Docker.
- [ ] Copiar la carpeta `data/`.
- [ ] Copiar la carpeta `uploads/`.
- [ ] Copiar el archivo `.env`.
- [ ] Guardar la copia con fecha.
- [ ] Arrancar Docker de nuevo.

---

## 10. Checklist final de aceptacion

- [ ] La aplicacion funciona desde el servidor.
- [ ] La aplicacion funciona desde otro portatil.
- [ ] `APP_BASE_URL` esta configurado con una URL accesible.
- [ ] Los QR abren ficha publica.
- [ ] La importacion Excel genera previsualizacion.
- [ ] La aplicacion permite aplicar solo filas seleccionadas.
- [ ] Las etiquetas Avery se generan correctamente.
- [ ] La carpeta `uploads` es persistente.
- [ ] La base SQLite esta en una ruta persistente.
- [ ] Existe una copia de seguridad inicial.

