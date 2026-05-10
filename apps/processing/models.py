import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    EXPIRED = "EXPIRED", "Expired"


class ProcessingTool(models.TextChoices):
    PDF_MERGE = "PDF_MERGE", "Merge PDF"
    PDF_SPLIT = "PDF_SPLIT", "Split PDF"
    PDF_ROTATE = "PDF_ROTATE", "Rotate PDF"
    PDF_TO_IMAGES = "PDF_TO_IMAGES", "PDF to Images"
    IMAGES_TO_PDF = "IMAGES_TO_PDF", "Images to PDF"
    PDF_REMOVE_RESTRICTIONS = "PDF_REMOVE_RESTRICTIONS", "Remove Restrictions"
    PDF_ENCRYPT = "PDF_ENCRYPT", "Encrypt PDF"
    PDF_DECRYPT = "PDF_DECRYPT", "Decrypt PDF"
    PDF_SANITIZE = "PDF_SANITIZE", "Sanitize PDF"
    PDF_FIND_AND_REDACT = "PDF_FIND_AND_REDACT", "Find And Redact"
    PDF_REMOVE_METADATA = "PDF_REMOVE_METADATA", "Remove Metadata"
    PDF_CHANGE_PERMISSIONS = "PDF_CHANGE_PERMISSIONS", "Change Permissions"
    PDF_FLATTEN = "PDF_FLATTEN", "Flatten PDF"

    IMAGE_CONVERT = "IMAGE_CONVERT", "Convert Image"
    IMAGE_RESIZE = "IMAGE_RESIZE", "Resize Image"
    IMAGE_COMPRESS = "IMAGE_COMPRESS", "Compress Image"
    IMAGE_ROTATE_FLIP = "IMAGE_ROTATE_FLIP", "Rotate or Flip Image"
    IMAGE_CROP = "IMAGE_CROP", "Crop Image"
    IMAGE_CONVERT_TO_JPG = "IMAGE_CONVERT_TO_JPG", "Convert To JPG"
    IMAGE_CONVERT_FROM_JPG = "IMAGE_CONVERT_FROM_JPG", "Convert From JPG"
    IMAGE_ROTATE_BATCH = "IMAGE_ROTATE_BATCH", "Rotate Images Batch"


class ProcessingJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processing_jobs",
    )

    tool = models.CharField(max_length=50, choices=ProcessingTool.choices)

    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )

    original_filename = models.CharField(max_length=255, blank=True)

    input_file = models.FileField(
        upload_to="processing/input/",
        null=True,
        blank=True,
    )

    output_file = models.FileField(
        upload_to="processing/output/",
        null=True,
        blank=True,
    )

    options = models.JSONField(default=dict, blank=True)

    error_message = models.TextField(blank=True)

    input_size = models.PositiveBigIntegerField(default=0)
    output_size = models.PositiveBigIntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["tool"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.tool} - {self.status}"


class ProcessingJobFile(models.Model):
    job = models.ForeignKey(
        ProcessingJob,
        on_delete=models.CASCADE,
        related_name="input_files",
    )
    file = models.FileField(upload_to="processing/input/")
    original_filename = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.job_id})"
