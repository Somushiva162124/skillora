from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),  # Handles login, logout, etc.
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('core.urls')),  # Main app's URL configuration
]

# Serving media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Add this line for static files
