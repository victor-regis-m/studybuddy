from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('room/<int:pk>/', views.room, name='room'),
    path('create-room/', views.create_room, name='create-room'),
    path('update-room/<int:pk>/', views.update_room, name='update-room'),
    path('delete-room/<int:pk>/', views.delete_room, name='delete-room'),
    path('user-profile/<int:pk>/', views.user_profile, name='user-profile'),
    path('delete-message/<int:pk>/', views.delete_message, name='delete-message'),
    path('update-user/', views.update_user  , name='update-user'),
    path('login', views.login_page, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout_view, name='logout'),
    path('topics', views.topics_page, name='topics'),
    path('activity', views.activity_page, name='activity')
]
