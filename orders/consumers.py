import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')

        # 1. Validar que el usuario esté autenticado
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4403)
            return

        self.user_group = f'user_{self.user.id}'
        self.admin_group = 'order_administrators'

        # 2. Suscribir al usuario a su canal individual (clientes y admins)
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        # 3. Comprobar permisos de gestión/administración
        self.is_order_manager = (
            self.user.is_superuser
            or self.user.is_staff
            or await self.user.groups.filter(
                name__in=['Administrador', 'Cajero']
            ).aexists()
        )

        # 4. Solo si es administrador o cajero, se suscribe al grupo global de pedidos
        if self.is_order_manager:
            await self.channel_layer.group_add(
                self.admin_group,
                self.channel_name
            )

        # Aceptar la conexión para TODOS los usuarios autenticados
        await self.accept()

    async def disconnect(self, close_code):
        # Remueve al usuario de su grupo individual
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

        # Remueve al usuario del grupo de administradores si pertenecía a él
        if getattr(self, 'is_order_manager', False):
            await self.channel_layer.group_discard(
                self.admin_group,
                self.channel_name
            )

    # Maneja eventos de creación de pedidos (order_created_event)
    async def order_created_event(self, event):
        payload = event.get('data', {k: v for k, v in event.items() if k != 'type'})
        await self.send(text_data=json.dumps(payload))

    # Maneja eventos de cambio de estado de pedidos (order_updated)
    async def order_updated(self, event):
        payload = event.get('data', {k: v for k, v in event.items() if k != 'type'})
        await self.send(text_data=json.dumps(payload))