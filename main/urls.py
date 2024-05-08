from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('gabean/', views.gabean, name='gabean'),
    path('syugpt/', views.syugpt, name='syugpt'),
]