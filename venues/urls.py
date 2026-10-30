from django.urls import path
from .views import (
    VenueListView,
    VenueDetailView,
    VenueCreateView,
    VenueUpdateView,
    VenueDeleteView,
)

app_name = 'venues'

urlpatterns = [
    path('', VenueListView.as_view(), name='list'),
    path('<int:pk>/', VenueDetailView.as_view(), name='detail'),
    path('create/', VenueCreateView.as_view(), name='create'),
    path('update/<int:pk>', VenueUpdateView.as_view(), name='update'),
    path('delete/<int:pk>', VenueDeleteView.as_view(), name='delete'),
]

