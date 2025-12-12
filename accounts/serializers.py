from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import SchemaUpload, GenerationResult


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    date_joined = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    last_login = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True, allow_null=True)
    datasets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'date_joined', 'last_login', 'datasets_count']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'datasets_count']
    
    def get_datasets_count(self, obj):
        """Return the number of datasets created by the user"""
        return SchemaUpload.objects.filter(user=obj).count()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def validate_email(self, value):
        """Ensure email is unique"""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("این ایمیل قبلاً استفاده شده است.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Validate that new password and confirm password match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'رمز عبور جدید و تأیید آن مطابقت ندارند.'
            })
        return attrs
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('رمز عبور فعلی اشتباه است.')
        return value


class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for user datasets"""
    db_type_display = serializers.CharField(source='get_db_type_display', read_only=True)
    
    class Meta:
        model = SchemaUpload
        fields = ['id', 'db_type', 'db_type_display', 'num_records', 
                  'uploaded_at', 'schema_file']
        read_only_fields = ['id', 'uploaded_at']


class DownloadSerializer(serializers.ModelSerializer):
    """Serializer for user SQL file downloads"""
    schema_id = serializers.IntegerField(source='schema.id', read_only=True)
    schema_db_type = serializers.CharField(source='schema.db_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = GenerationResult
        fields = ['id', 'schema_id', 'schema_db_type', 'output_file', 
                  'status', 'status_display', 'generated_at', 'file_name', 'file_size']
        read_only_fields = ['id', 'generated_at']
    
    def get_file_name(self, obj):
        """Get the file name from the file path"""
        if obj.output_file:
            return obj.output_file.name.split('/')[-1]
        return None
    
    def get_file_size(self, obj):
        """Get the file size in bytes"""
        if obj.output_file and obj.output_file.storage.exists(obj.output_file.name):
            return obj.output_file.size
        return None
