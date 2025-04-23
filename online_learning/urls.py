from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import maintenance

urlpatterns = []

if settings.MAINTENANCE_MODE:
    urlpatterns += [
        path('', maintenance),
    ]
else:
    urlpatterns += [
        path('', include('core.urls')),
        path('admin/', admin.site.urls),
        path('accounts/', include('django.contrib.auth.urls')),
        path('ckeditor5/', include('django_ckeditor_5.urls')),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
