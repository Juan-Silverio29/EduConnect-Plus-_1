# auth_app/api_urls.py
from django.urls import path
from .api_views import register_api, MyTokenObtainPairView, refresh_token

urlpatterns = [
    path("register/", register_api, name="api-register"),
    path("login/", MyTokenObtainPairView.as_view(), name="api-login"),
    path("refresh/", refresh_token, name="api-refresh"),
]
