from django.urls import path
from . import views
# users/urls.py
app_name='users'
urlpatterns = [
    path('', views.UserListView.as_view(), name='list'),
    path('create/', views.UserCreateView.as_view(), name='create'),
    path('<int:pk>/detail/', views.UserDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.UserDeleteView.as_view(), name='delete'),
    path('<int:pk>/restore/', views.UserRestoreView.as_view(), name='restore'),
    path('<int:pk>/', views.UserUpdateView.as_view(), name='update'),
    path('home/', views.dashboard_view, name='home'),

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path(
        'profile/password/',
        views.UserPasswordChangeView.as_view(),
        name='password_change'
    ),
]