from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.converters.exceptions import ConverterError

from .models import ProcessingJob, ProcessingStatus
from .serializers import ProcessingJobSerializer
from .services import (
    enqueue_pdf_to_images_job,
    run_image_compress_job,
    run_image_convert_job,
    run_image_resize_job,
    run_image_rotate_flip_job,
    run_images_to_pdf_job,
    run_pdf_merge_job,
    run_pdf_rotate_job,
    run_pdf_split_job,
    run_pdf_to_images_job,
)
from apps.processing.models import ProcessingJob
from apps.processing.services import attach_uploaded_files_to_job
from apps.processing.tasks import process_pdf_merge_job


class PdfMergeView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")

        try:
            job = run_pdf_merge_job(
                user=request.user,
                uploaded_files=uploaded_files,
            )

            return Response(
                ProcessingJobSerializer(
                    job,
                    context={"request": request},
                ).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            job = ProcessingJob.objects.order_by("-created_at").first()

            return Response(
                {
                    "detail": str(exc),
                    "job": ProcessingJobSerializer(
                        job,
                        context={"request": request},
                    ).data
                    if job
                    else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la fusion PDF."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProcessingJobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = ProcessingJob.objects.filter(user=request.user).order_by("-created_at")

        serializer = ProcessingJobSerializer(
            jobs,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)


class ProcessingJobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        try:
            job = ProcessingJob.objects.get(id=job_id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Job introuvable.")

        serializer = ProcessingJobSerializer(
            job,
            context={"request": request},
        )

        return Response(serializer.data)


class ProcessingJobDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        try:
            job = ProcessingJob.objects.get(id=job_id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Job introuvable.")

        if job.status != ProcessingStatus.COMPLETED:
            return Response(
                {"detail": "Le fichier n'est pas encore disponible."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not job.output_file:
            return Response(
                {"detail": "Aucun fichier de sortie disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not job.output_file.storage.exists(job.output_file.name):
            return Response(
                {"detail": "Le fichier résultat n'existe plus."},
                status=status.HTTP_404_NOT_FOUND,
            )

        filename = job.output_file.name.split("/")[-1]

        return FileResponse(
            job.output_file.open("rb"),
            as_attachment=True,
            filename=filename,
        )


class ImageConvertView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer une image avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "output_format": request.data.get("output_format", "webp"),
            "quality": request.data.get("quality", 85),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_convert_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(
                    job,
                    context={"request": request},
                ).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la conversion image."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImageResizeView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer une image avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "width": request.data.get("width"),
            "height": request.data.get("height"),
            "keep_ratio": request.data.get("keep_ratio", "true"),
            "output_format": request.data.get("output_format", "webp"),
            "quality": request.data.get("quality", 85),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_resize_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(
                    job,
                    context={"request": request},
                ).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant le redimensionnement image."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImageCompressView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer une image avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "output_format": request.data.get("output_format", "webp"),
            "quality": request.data.get("quality", 75),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_compress_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"detail": "Une erreur serveur est survenue pendant la compression image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImageRotateFlipView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer une image avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "operation": request.data.get("operation", "rotate_90"),
            "output_format": request.data.get("output_format", "webp"),
            "quality": request.data.get("quality", 85),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_rotate_flip_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la rotation ou le flip image."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImagesToPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")

        if not uploaded_files:
            return Response(
                {"detail": "Veuillez envoyer une ou plusieurs images avec le champ 'files'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "page_size": request.data.get("page_size", "auto"),
            "orientation": request.data.get("orientation", "portrait"),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_images_to_pdf_job(
                user=request.user,
                uploaded_files=uploaded_files,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la conversion images vers PDF."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        

class PdfSplitView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer un PDF avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "mode": request.data.get("mode", "all"),
            "pages": request.data.get("pages", ""),
        }

        try:
            job = run_pdf_split_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"detail": "Une erreur serveur est survenue pendant la division PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PdfRotateView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer un PDF avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "angle": request.data.get("angle", 90),
            "pages": request.data.get("pages", "all"),
        }

        try:
            job = run_pdf_rotate_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"detail": "Une erreur serveur est survenue pendant la rotation PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PdfToImagesView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer un PDF avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "output_format": request.data.get("output_format", "png"),
            "scale": request.data.get("scale", 2.0),
        }

        try:
            job = enqueue_pdf_to_images_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la conversion PDF vers images.",
                    "error": str(exc),
                    "type": exc.__class__.__name__,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class PdfMergeAsyncView(APIView):
    def post(self, request):
        files = request.FILES.getlist("files")

        if len(files) < 2:
            return Response(
                {"detail": "Please upload at least two PDF files."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for uploaded_file in files:
            if uploaded_file.content_type != "application/pdf":
                return Response(
                    {"detail": "Only PDF files are allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        job = ProcessingJob.objects.create(
            tool="PDF_MERGE",
            status="PENDING",
        )

        attach_uploaded_files_to_job(job, files)

        process_pdf_merge_job.delay(str(job.id))

        return Response(
            {
                "job_id": str(job.id),
                "status": job.status,
                "tool": job.tool,
            },
            status=status.HTTP_202_ACCEPTED,
        )






































