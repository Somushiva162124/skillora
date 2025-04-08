from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include the authentication URLs (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),  # Handles login, logout, etc.
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    
    # Your app's URLs
    path('', include('core.urls')),  # Main app's URL configuration
]

# Serve static files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
