from django.urls import path

from .views import (
    HallCreateView,
    HallDeleteView,
    HallDetailView,
    HallListView,
    HallUpdateView,
)

app_name = 'halls'

urlpatterns = [
    path('', HallListView.as_view(), name='list'),
    path('create/', HallCreateView.as_view(), name='create'),
    path('<int:pk>/', HallDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', HallUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', HallDeleteView.as_view(), name='delete'),
]
