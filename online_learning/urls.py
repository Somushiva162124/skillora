from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import maintenance  # Make sure your maintenance view is correct

urlpatterns = [
    # Maintenance Mode URL should come first
    path('', maintenance),  # If maintenance is enabled, this will block access to other pages.

    # Admin
    path('admin/', admin.site.urls),

    # Core app URLs
    path('', include('core.urls')),  # Main app's URL configuration

    # Auth URLs (This includes login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # CKEditor URL
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

# Serving media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
