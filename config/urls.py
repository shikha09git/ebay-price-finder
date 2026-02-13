"""
URL configuration for eBay Price Finder project.
"""
from django.contrib import admin
from django.urls import path, include
from finder import views as finder_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/signup/', finder_views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('finder.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
