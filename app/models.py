import base64
from django.db import models
from django.utils.timezone import now
from PIL import Image

class UserProfile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    encode_photos = models.TextField(null=True, blank=True)
    create_time = models.DateTimeField(default=now, editable=False)
    update_time = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class Attendance(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="attendance_records")
    timestamp = models.DateTimeField(default=now)
    status = models.CharField(max_length=50, default="Present")