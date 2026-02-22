from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# در حال حاضر از User model خود Django استفاده می‌کنیم
# اگر نیاز به فیلدهای اضافی برای User دارید، می‌توانید از UserProfile استفاده کنید:

# class UserProfile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
#     phone_number = models.CharField(max_length=20, blank=True, null=True)
#     bio = models.TextField(blank=True, null=True)
#     avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
# 
#     def __str__(self):
#         return f"Profile of {self.user.username}"

# برای حال حاضر، این فایل خالی می‌ماند چون از User model خود Django استفاده می‌کنیم
