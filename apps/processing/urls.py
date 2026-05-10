from django.urls import path

from .image_views import (
    ImageConvertFromJpgView,
    ImageConvertToJpgView,
    ImageCropView,
    ImageRotateBatchView,
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
