from django.urls import path
from . import views

app_name = 'finder'

urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add_product, name='add_product'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('accounts/guest/', views.guest_login, name='guest_login'),
    path('upload/', views.upload_image, name='upload'),
    path('search/', views.manual_search, name='manual_search'),
    path('results/<int:pk>/', views.results, name='results'),
    path('refresh/<int:pk>/', views.refresh_search, name='refresh'),
    path('api/search/', views.api_search, name='api_search'),
]
