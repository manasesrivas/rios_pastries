# Rios pastries backend


# comandos

para encender el servidor:
```bash
python manage.py runserver
```

## Reenvío de verificación

En el detalle de un usuario con acceso deshabilitado y que no esté eliminado,
un administrador con permisos de gestión de usuarios o un superusuario puede
reenviar el correo de verificación. El envío no habilita la cuenta: el enlace
lo hará cuando el destinatario lo abra. Antes de reenviarlo, comprueba el motivo
de la deshabilitación; el sistema no distingue una cuenta pendiente de verificar
de una deshabilitada por otra causa.

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

## API de reservaciones

`GET /api/reservations/` requiere autenticación JWT y el permiso
`view_reservation`. Los usuarios consultan sus reservaciones; Administrador y
Cajero pueden consultar todas. Las reservaciones eliminadas no aparecen en el
listado. La respuesta incluye el ID de `sala`, el nombre de la sala y los datos
del local asociado; `hall` y `venue` se devuelven como `null`.

`POST /api/reservations/` crea una reservación con los productos indicados.
Requiere JWT y el permiso `reservations.add_reservation`. La ruta anterior
`POST /api/reservations/create/` sigue disponible. El servidor asigna el
cliente autenticado, confirma la reservación, consolida productos repetidos
y obtiene los precios de la base de datos. No se aplica horario comercial.
Por defecto se permiten reservaciones sin productos: envía `items: []` o
omite el campo. Para exigir al menos uno, configura
`RESERVATIONS_REQUIRE_PRODUCTS = True` en Django.
En SQLite, `select_for_update()` no bloquea filas: bajo concurrencia puede
producirse un error de base de datos bloqueada. Para bloqueo por fila se
requiere una base de datos compatible; la restricción única condicional también
debe estar soportada por el motor elegido.

Ejemplo de petición (elige una fecha futura y IDs existentes):

```http
POST /api/reservations/
Authorization: Bearer <token>
Content-Type: application/json

{
  "fecha_evento": "2026-12-20",
  "cantidad_personas": 50,
  "sala": 3,
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 5, "quantity": 1}
  ]
}
```

Ejemplo de respuesta `201 Created`:

```json
{
  "id": 10,
  "cliente": 4,
  "fecha_evento": "2026-12-20",
  "cantidad_personas": 50,
  "sala": 3,
  "estado": "CONFIRMADA",
  "hallName": "Salón principal",
  "venueName": "Centro de eventos",
  "venueAdress": "San Salvador",
  "hall": null,
  "venue": null,
  "total_productos": "30.00",
  "items": [
    {"product": 1, "name": "Pastel", "quantity": 2, "price": "12.50", "subtotal": "25.00"},
    {"product": 5, "name": "Mesa extra", "quantity": 1, "price": "5.00", "subtotal": "5.00"}
  ]
}
```

Los errores de reservación y disponibilidad pueden aparecer juntos en una
respuesta `400 Bad Request`:

```json
{
  "fecha_evento": ["Esta sala ya tiene una reservación activa para esa fecha."],
  "items": [
    {"product_id": 3, "name": "Pastel", "error": "El producto \"Pastel\" no está disponible actualmente."},
    {"product_id": 7, "name": null, "error": "El producto no existe o fue eliminado."}
  ]
}
```

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
