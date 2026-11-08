from .utils import is_store_open

def store_status(request):
    return {
        'is_store_open': is_store_open()
    }