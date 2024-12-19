from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-team/', views.create_team, name='create_team'),
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('pokemon/<str:pokemon_name>/', views.pokemon_detail, name='pokemon_detail'),
    path('team/<int:team_id>/analysis/', views.team_analysis, name='team_analysis'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
]
