from django.urls import path
from . import views

app_name = 'main_mobile'

urlpatterns = [
    path('', views.mobile_home.as_view(), name='m_home'),
]
