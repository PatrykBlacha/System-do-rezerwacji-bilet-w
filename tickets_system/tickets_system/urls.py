from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.contrib.auth import views as auth_views
from tickets_app.views import IndexView
from tickets_app.views import register

urlpatterns = [
    path('', IndexView.as_view(), name='home'),
    path("", include("tickets_app.urls")),
    path("admin/", admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/register/', register, name='register')
]
