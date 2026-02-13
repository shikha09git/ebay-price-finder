from django.urls import path
from . import views

app_name = 'finder'

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/guest/', views.guest_login, name='guest_login'),
    path('upload/', views.upload_image, name='upload'),
    path('search/', views.manual_search, name='manual_search'),
    path('results/<int:pk>/', views.results, name='results'),
    path('refresh/<int:pk>/', views.refresh_search, name='refresh'),
    path('api/search/', views.api_search, name='api_search'),
]
