from django.db import models
from django.conf import settings

class SchemaUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    schema_file = models.FileField(upload_to='schemas/')
    db_type = models.CharField(max_length=50, choices=[('mysql', 'MySQL'), ('postgres', 'PostgreSQL')], default='mysql')
    num_records = models.PositiveIntegerField(default=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schema {self.id} - {self.db_type}"

class GenerationResult(models.Model):
    schema = models.ForeignKey(SchemaUpload, on_delete=models.CASCADE, related_name='results')
    output_file = models.FileField(upload_to='outputs/')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')
    error_message = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result {self.id} - {self.status}"

class TaskLog(models.Model):
    task_id = models.CharField(max_length=255)
    schema = models.ForeignKey(SchemaUpload, on_delete=models.CASCADE)
    log_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)