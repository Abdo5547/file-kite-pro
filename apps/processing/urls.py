from django.urls import path

from .views import (
    ImageCompressView,
    ImageConvertView,
    ImageResizeView,
    ImageRotateFlipView,
    ImagesToPdfView,
    PdfAddBlankPageView,
    PdfDeletePagesView,
    PdfExtractPagesView,
    PdfMergeAsyncView,
    PdfMergeView,
    PdfOrganizeView,
    PdfReversePagesView,
    PdfRotateCustomView,
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
    path("pdf/delete-pages/", PdfDeletePagesView.as_view(), name="pdf-delete-pages"),
    path("pdf/extract-pages/", PdfExtractPagesView.as_view(), name="pdf-extract-pages"),
    path("pdf/organize/", PdfOrganizeView.as_view(), name="pdf-organize"),
    path("pdf/rotate-custom/", PdfRotateCustomView.as_view(), name="pdf-rotate-custom"),
    path("pdf/add-blank-page/", PdfAddBlankPageView.as_view(), name="pdf-add-blank-page"),
    path("pdf/reverse-pages/", PdfReversePagesView.as_view(), name="pdf-reverse-pages"),
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
    path("images/resize/", ImageResizeView.as_view(), name="image-resize"),
    path("images/compress/", ImageCompressView.as_view(), name="image-compress"),
    path("images/rotate-flip/", ImageRotateFlipView.as_view(), name="image-rotate-flip"),
]