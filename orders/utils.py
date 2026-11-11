from datetime import time
from django.utils import timezone

OPENING_TIME = time(9, 0, 0)   # 09:00 AM
CLOSING_TIME = time(23, 0, 0)  # 07:00 PM (19:00 HS)

def is_store_open() -> bool:
    """
    Retorna True si la hora actual está dentro del rango 09:00 - 19:00.
    """
    current_time = timezone.localtime(timezone.now()).time()
    return OPENING_TIME <= current_time <= CLOSING_TIME