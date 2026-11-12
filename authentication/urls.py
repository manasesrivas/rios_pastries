from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.urls import reverse_lazy

#authentication/urls.py
app_name='authentication'
urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.UsersCreateView.as_view(), name='register'),
    path('app/', views.apk_page, name='apk_page'),
    path('app/download/', views.apk_download, name='apk_download'),
    
    path('verification-sent/', TemplateView.as_view(
        template_name='authentication/verification_sent.html',
    ), name='verification_sent'),

    path('activate/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='activate'),

    # ========= password reset ===============

    path('password-reset/', views.AuthenticationResetPasswordView.as_view(), name='password_reset'),
        path('reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='password_reset/password_reset_confirm.html',
             success_url=reverse_lazy('authentication:password_reset_complete'),
         ),
         name='password_reset_confirm'),

    path('password-reset/done/',
         PasswordResetDoneView.as_view(
             template_name='password_reset/password_reset_done.html',
         ),
         name='password_reset_done'),


    path('reset/done/',
         PasswordResetCompleteView.as_view(
             template_name='password_reset/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]