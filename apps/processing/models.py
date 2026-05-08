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
    PDF_DELETE_PAGES = "PDF_DELETE_PAGES", "Delete Pages"
    PDF_EXTRACT_PAGES = "PDF_EXTRACT_PAGES", "Extract Pages"
    PDF_ORGANIZE = "PDF_ORGANIZE", "Organize PDF"
    PDF_ROTATE = "PDF_ROTATE", "Rotate PDF"
    PDF_ROTATE_CUSTOM = "PDF_ROTATE_CUSTOM", "Rotate Custom"
    PDF_ADD_BLANK_PAGE = "PDF_ADD_BLANK_PAGE", "Add Blank Page"
    PDF_REVERSE_PAGES = "PDF_REVERSE_PAGES", "Reverse Pages"
    PDF_N_UP = "PDF_N_UP", "N-Up PDF"
    PDF_GRID_COMBINE = "PDF_GRID_COMBINE", "Grid Combine"
    PDF_ALTERNATE_MERGE = "PDF_ALTERNATE_MERGE", "Alternate Merge"
    PDF_DIVIDE_PAGES = "PDF_DIVIDE_PAGES", "Divide Pages"
    PDF_COMBINE_SINGLE_PAGE = "PDF_COMBINE_SINGLE_PAGE", "Combine Single Page"
    PDF_POSTERIZE = "PDF_POSTERIZE", "Posterize PDF"
    PDF_MULTI_TOOL = "PDF_MULTI_TOOL", "PDF Multi Tool"
    PDF_ADD_ATTACHMENTS = "PDF_ADD_ATTACHMENTS", "Add Attachments"
    PDF_EXTRACT_ATTACHMENTS = "PDF_EXTRACT_ATTACHMENTS", "Extract Attachments"
    PDF_TO_IMAGES = "PDF_TO_IMAGES", "PDF to Images"
    IMAGES_TO_PDF = "IMAGES_TO_PDF", "Images to PDF"

    IMAGE_CONVERT = "IMAGE_CONVERT", "Convert Image"
    IMAGE_RESIZE = "IMAGE_RESIZE", "Resize Image"
    IMAGE_COMPRESS = "IMAGE_COMPRESS", "Compress Image"
    IMAGE_ROTATE_FLIP = "IMAGE_ROTATE_FLIP", "Rotate or Flip Image"


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
