from django.urls import path

from .image_views import (
    ImageConvertFromJpgView,
    ImageConvertToJpgView,
    ImageCropView,
    ImageRotateBatchView,
)
from .pdf_security_views import (
    ChangePermissionsPdfView,
    DecryptPdfView,
    EncryptPdfView,
    FlattenPdfView,
    FindAndRedactPdfView,
    RemoveMetadataPdfView,
    RemoveRestrictionsPdfView,
    SanitizePdfView,
)
from .views import (
    ImageCompressView,
    ImageConvertView,
    ImageResizeView,
    ImageRotateFlipView,
    ImagesToPdfView,
    PdfMergeAsyncView,
    PdfMergeView,
    PdfRotateView,
    PdfSplitView,
    PdfToImagesView,
    ProcessingJobDetailView,
    ProcessingJobDownloadView,
    ProcessingJobListView,
)


app_name = "processing"

urlpatterns = [
    path("pdf/merge/", PdfMergeView.as_view(), name="pdf-merge"),
    path("pdf/images-to-pdf/", ImagesToPdfView.as_view(), name="images-to-pdf"),
    path("pdf/split/", PdfSplitView.as_view(), name="pdf-split"),
    path("pdf/rotate/", PdfRotateView.as_view(), name="pdf-rotate"),
    path("pdf/to-images/", PdfToImagesView.as_view(), name="pdf-to-images"),
    path("pdf/merge/async/", PdfMergeAsyncView.as_view(), name="pdf-merge-async"),
    path("pdf/remove-restrictions/", RemoveRestrictionsPdfView.as_view(), name="pdf-remove-restrictions"),
    path("pdf/encrypt/", EncryptPdfView.as_view(), name="pdf-encrypt"),
    path("pdf/decrypt/", DecryptPdfView.as_view(), name="pdf-decrypt"),
    path("pdf/sanitize/", SanitizePdfView.as_view(), name="pdf-sanitize"),
    path("pdf/find-and-redact/", FindAndRedactPdfView.as_view(), name="pdf-find-and-redact"),
    path("pdf/remove-metadata/", RemoveMetadataPdfView.as_view(), name="pdf-remove-metadata"),
    path("pdf/change-permissions/", ChangePermissionsPdfView.as_view(), name="pdf-change-permissions"),
    path("pdf/flatten/", FlattenPdfView.as_view(), name="pdf-flatten"),
    path("jobs/", ProcessingJobListView.as_view(), name="job-list"),
    path("jobs/<uuid:job_id>/", ProcessingJobDetailView.as_view(), name="job-detail"),
    path(
        "jobs/<uuid:job_id>/download/",
        ProcessingJobDownloadView.as_view(),
        name="job-download",
    ),
    path("images/convert/", ImageConvertView.as_view(), name="image-convert"),
    path("images/convert-to-jpg/", ImageConvertToJpgView.as_view(), name="image-convert-to-jpg"),
    path("images/convert-from-jpg/", ImageConvertFromJpgView.as_view(), name="image-convert-from-jpg"),
    path("images/resize/", ImageResizeView.as_view(), name="image-resize"),
    path("images/compress/", ImageCompressView.as_view(), name="image-compress"),
    path("images/rotate-flip/", ImageRotateFlipView.as_view(), name="image-rotate-flip"),
    path("images/rotate-batch/", ImageRotateBatchView.as_view(), name="image-rotate-batch"),
    path("images/crop/", ImageCropView.as_view(), name="image-crop"),
]
