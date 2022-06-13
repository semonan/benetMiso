from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('temperature_max/', views.temperature_max),
    path('current_capture/', views.current_capture),
]
