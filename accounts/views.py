from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from core.models import SchemaUpload, GenerationResult

from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    DatasetSerializer,
    DownloadSerializer
)


# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    GET /api/user/profile
    دریافت اطلاعات پروفایل کاربر
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    PATCH /api/user/profile/update
    به‌روزرسانی اطلاعات پروفایل کاربر
    """
    serializer = UserProfileUpdateSerializer(
        request.user, 
        data=request.data, 
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'پروفایل با موفقیت به‌روزرسانی شد.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    PATCH /api/user/change-password
    تغییر رمز عبور کاربر
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # به‌روزرسانی session برای جلوگیری از logout شدن
        update_session_auth_hash(request, user)
        
        return Response({
            'message': 'رمز عبور با موفقیت تغییر یافت.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_datasets(request):
    """
    GET /api/user/my-datasets
    دریافت لیست دیتاست‌های کاربر
    """
    datasets = SchemaUpload.objects.filter(user=request.user).order_by('-uploaded_at')
    serializer = DatasetSerializer(datasets, many=True)
    return Response({
        'count': datasets.count(),
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_downloads(request):
    """
    GET /api/user/my-downloads
    دریافت لیست فایل‌های SQL تولیدشده کاربر
    """
    # دریافت تمام GenerationResult هایی که schema آن‌ها متعلق به کاربر است
    downloads = GenerationResult.objects.filter(
        schema__user=request.user
    ).select_related('schema').order_by('-generated_at')
    
    serializer = DownloadSerializer(downloads, many=True)
    return Response({
        'count': downloads.count(),
        'results': serializer.data
    }, status=status.HTTP_200_OK)
