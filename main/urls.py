from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('blog/', views.board_list, name='board_list'),
    path('blog/board/new/', views.board_create, name='board_create'),
    path('blog/board/<slug:board_slug>/', views.post_list, name='post_list'),
    path('blog/board/<slug:board_slug>/edit/', views.board_edit, name='board_edit'),
    path('blog/board/<slug:board_slug>/delete/', views.board_delete, name='board_delete'),
    path('blog/board/<slug:board_slug>/post/new/', views.post_create, name='post_create'),
    path('blog/board/<slug:board_slug>/post/<slug:post_slug>/', views.post_detail, name='post_detail'),
    path('blog/board/<slug:board_slug>/post/<slug:post_slug>/edit/', views.post_edit, name='post_edit'),
    path('blog/board/<slug:board_slug>/post/<slug:post_slug>/delete/', views.post_delete, name='post_delete'),
]
