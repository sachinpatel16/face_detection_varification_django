from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from app import views
urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    # path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('', views.home, name='home'),
    path('login', views.login, name='login'),
    path('chat/', views.chat, name="chat"),
    path('att/', views.mark_attendance, name='make_attendance'),
    # path("", include("facedetect.urls"))  # Include app URLs
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
