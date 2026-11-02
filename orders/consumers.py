import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NoticationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4403)
            return

        is_order_manager = (
            user.is_superuser
            or user.is_staff
            or await user.groups.filter(
                name__in=['Administrador', 'Cajero']
            ).aexists()
        )
        if not is_order_manager:
            await self.close(code=4403)
            return

        self.group_name = 'order_administrators'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def order_updated(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'type': 'order_updated',
                    'order_id': event['order_id'],
                    'product_name': event['product_name'],
                }
            )
        )