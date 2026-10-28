from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.api_chat, name='ai_chat'),            # POST -> {message}
    path('history/', views.get_history, name='ai_history'),   # GET -> historial
    path('stats/', views.ai_stats, name='ai_stats'),          # GET -> métricas para Plotly
]
