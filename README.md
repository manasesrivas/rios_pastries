# Rios pastries backend


# comandos

para encender el servidor:
```bash
python manage.py runserver
```

## API de productos

Instala las dependencias del proyecto (incluye Django REST Framework):
```bash
python -m pip install -r requirements.txt
```

La ruta `GET /api/products/` lista los productos disponibles sin requerir
autenticación. Para modificar productos, inicia sesión y usa la ruta
`/api/products/<id>/`:

- `POST /api/products/` crea un producto (requiere el permiso `add_product`).
- `PUT` o `PATCH /api/products/<id>/` actualiza un producto (requiere
  `change_product`).
- `DELETE /api/products/<id>/` elimina un producto (requiere `delete_product`).

## API de órdenes

Las rutas de órdenes requieren enviar el token JWT en el encabezado
`Authorization: Bearer <token>` y los permisos `view_order` o `add_order`.

- `POST /api/orders/validate/` valida la disponibilidad del carrito, sin
  guardar cambios.
- `GET /api/orders/` lista las órdenes del usuario autenticado.
- `POST /api/orders/` valida nuevamente el carrito y crea el pedido y sus
  detalles en una transacción. Envía `metodo_pago`, `tipo_entrega`,
  opcionalmente `direccion`, y una lista `items` con `product_id` y `quantity`.
  El servidor obtiene los precios de la base de datos.
- Puedes enviar `Idempotency-Key` en la cabecera para que un reintento idéntico
  no cree otra orden.

Ambos endpoints POST responden `409 Conflict` con el código
`CART_UNAVAILABLE_PRODUCTS` y la lista de productos inválidos si alguno no
existe, fue eliminado o no está disponible.

Ejemplo de cuerpo:
```json
{
  "metodo_pago": "efectivo",
  "tipo_entrega": "recoger",
  "items": [
    {"product_id": 1, "quantity": 2}
  ]
}
```

## API de salas

`GET /api/halls/` y `GET /api/halls/<id>/` requieren autenticación JWT y el
permiso `view_hall`. Además de `venueName`, cada sala incluye `venue` con
`id`, `name`, `address`, `descripcion` y `status` del local.

## API de reservaciones

`GET /api/reservations/` requiere autenticación JWT y el permiso
`view_reservation`. Los usuarios consultan sus reservaciones; Administrador y
Cajero pueden consultar todas. Las reservaciones eliminadas no aparecen en el
listado. La respuesta incluye el ID de `sala`, el nombre de la sala y los datos
del local asociado; `hall` y `venue` se devuelven como `null`.

## agregar un modulo al proyecto
`djando` trabaja mediante apps, para crear una app necesita escribir el siguiente codigo en la terminal:
```bash
python manage.py startapp [nombre_de_la_app]
```
en el caso en la que se creó la app `users` fue de la siguiente manera: 
```bash
python manage.py startapp users
```
luego registrarlo en el archivo `settings.py` en array `INSTALLED_APPS` agregar debajo la app creada para que django pueda reconocerla

comando para crear la migracion para los roles iniciales
```bash
python manage.py makemigrations [modulo] --empty -n [nombre_migracion]
```

## rutas
