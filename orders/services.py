from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def publish_order_update(**kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    # Notificar al personal/administradores (panel en tiempo real)
    async_to_sync(channel_layer.group_send)(
        'order_administrators',
        {
            'type': 'order_created_event',
            'data': kwargs
        }
    )

    # Notificar únicamente al cliente comprador (limpieza de localStorage)
    user_id = kwargs.get('user_id')
    if user_id:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'order_created_event',
                'data': kwargs
            }
        )