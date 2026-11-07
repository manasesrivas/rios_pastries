from halls.models import Hall
from venues.models import Venue
from colorama import Fore
venues = [
    {
        'name': 'Local #1',
        'address': 'San Miguel Centro, San Miguel',
        'descripcion': 'descripcion',
    },
    {
        'name': 'Local #2',
        'address': 'La Union Sur, La Union',
        'descripcion': 'descripcion',
    },
]

halls = [
    {
        'venue': 1,
        'name': 'Sala #1',
        'capacity': 100,
        'price': 100,
    },
    {
        'venue': 1,
        'name': 'Sala #2',
        'capacity': 100,
        'price': 100,
    },
    {
        'venue': 2,
        'name': 'Sala #1',
        'capacity': 150,
        'price': 150,
    },
    {
        'venue': 2,
        'name': 'Sala #2',
        'capacity': 150,
        'price': 150,
    }
]
def create_venues():
    for venue in venues:
        _, created = Venue.objects.get_or_create(
            name=venue['name'],
            address=venue['address'],
            descripcion=venue['descripcion']
        )
        if created: print(f'{Fore.GREEN}se ha creado {Fore.WHITE}{venue['name']}')
        else: print(f'{Fore.RED}no se pudo crear {Fore.WHITE}{venue['name']}')

def create_halls():
    for hall in halls:
        venue = Venue.objects.get(id=hall['venue'])
        _, created = Hall.objects.get_or_create(
            venue=venue,
            name=hall['name'],
            capacity=hall['capacity'],
            price=hall['price']
        )
        if created: print(f'{Fore.GREEN}se ha creado {Fore.WHITE}{hall['name']}')
        else: print(f'{Fore.RED}no se pudo crear {Fore.WHITE}{hall['name']}')
create_venues()
create_halls()