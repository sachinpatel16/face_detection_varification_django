from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from app import views
urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    # path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('', views.login, name='login'),
    # path("", include("facedetect.urls"))  # Include app URLs
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
