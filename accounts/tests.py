# accounts/tests.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import SchemaUpload, GenerationResult
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class UserProfileAPITest(APITestCase):

    def setUp(self):
        # ایجاد یک کاربر تستی
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.client = APIClient()

        # ایجاد یک دیتاست برای کاربر
        schema_file = SimpleUploadedFile("schema.sql", b"CREATE TABLE test(id INT);")
        self.dataset = SchemaUpload.objects.create(
            user=self.user,
            schema_file=schema_file,
            num_records=10,
            db_type="mysql"
        )

        # ایجاد یک نتیجه تولید SQL
        output_file = SimpleUploadedFile("output.sql", b"INSERT INTO test VALUES (1);")
        self.download = GenerationResult.objects.create(
            schema=self.dataset,
            output_file=output_file,
            status="completed"
        )

    def test_user_profile_authenticated(self):
        """تست دریافت پروفایل با احراز هویت"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/accounts/profile/')  # URL مستقیم
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        # بررسی وجود فیلدها
        self.assertIn('downloads_count', response.data)
        self.assertIn('datasets_count', response.data)
        self.assertEqual(response.data['datasets_count'], 1)
        self.assertEqual(response.data['downloads_count'], 1)

    def test_user_profile_unauthenticated(self):
        """تست دسترسی بدون احراز هویت - REST Framework 403 برمی‌گرداند نه 401"""
        url = reverse('user-profile')
        response = self.client.get(url)
        # REST Framework با SessionAuthentication، 403 برمی‌گرداند نه 401
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password(self):
        """تست تغییر رمز عبور"""
        self.client.force_authenticate(user=self.user)
        url = reverse('change-password')
        data = {
            "old_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_change_password_wrong_old(self):
        """تست تغییر رمز عبور با رمز قدیمی اشتباه"""
        self.client.force_authenticate(user=self.user)
        url = reverse('change-password')
        data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_downloads(self):
        """تست دریافت لیست دانلودها"""
        self.client.force_authenticate(user=self.user)
        url = reverse('my-downloads')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        # Django به فایل‌ها suffix اضافه می‌کند، پس از endswith استفاده می‌کنیم
        self.assertTrue(response.data['results'][0]['file_name'].endswith('output.sql'))
        # یا می‌توانیم فقط بررسی کنیم که فایل وجود دارد
        self.assertIsNotNone(response.data['results'][0]['file_name'])

    def test_my_datasets(self):
        """تست دریافت لیست دیتاست‌ها"""
        self.client.force_authenticate(user=self.user)
        url = reverse('my-datasets')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        # بررسی نام فایل - Django ممکن است suffix اضافه کند
        self.assertTrue(response.data['results'][0]['name'].endswith('schema.sql'))
        self.assertEqual(response.data['results'][0]['num_records'], 10)
