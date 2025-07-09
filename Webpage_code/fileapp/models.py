from django.db import models

# Create your models here.
from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to="")  # Remove 'uploads/' prefix
    s3_key = models.CharField(max_length=255, blank=True, null=True) 
    uploaded_at = models.DateTimeField(auto_now_add=True)

class FileModel(models.Model):
    file = models.FileField(upload_to='uploads/')
    s3_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file:
            # Store file.name or generate a unique key
            self.s3_key = self.file.name
        super().save(*args, **kwargs)
