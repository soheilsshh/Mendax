from django.urls import path
from . import views

app_name = 'accounts'  # اضافه کردن app_name

urlpatterns = [
    path('profile/', views.user_profile, name='user-profile'),
    path('change-password/', views.change_password, name='change-password'),
    path('my-downloads/', views.my_downloads, name='my-downloads'),
    path('my-datasets/', views.my_datasets, name='my-datasets'),
]
