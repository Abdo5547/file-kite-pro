from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.plans.limits import get_plan_limits

from .access import is_processing_job_token_valid
from .models import ProcessingJob, ProcessingStatus, ProcessingTool
from .serializers import ProcessingJobSerializer
from .services import (
    attach_uploaded_files_to_job,
    enqueue_pdf_to_images_job,
    get_job_user,
)
from .tasks import process_pdf_merge_job
from .validators import validate_pdf_uploaded_files
from .views import ANONYMOUS_JOB_SESSION_KEY
from apps.converters.exceptions import ConverterError


def _serialize_job(request, job):
    return ProcessingJobSerializer(job, context={"request": request}).data


def _get_processing_job_access_token(request):
    return (
        request.query_params.get("token")
        or request.headers.get("X-Processing-Job-Token")
        or request.headers.get("X-Processing-Token")
    )


def _request_has_session_access(request, job):
    session_job_ids = request.session.get(ANONYMOUS_JOB_SESSION_KEY, [])
    return str(job.id) in session_job_ids


def _is_request_authorized_for_job(request, job):
    if request.user.is_authenticated and job.user_id == request.user.id:
        return True

    token = _get_processing_job_access_token(request)
    if is_processing_job_token_valid(job, token):
        return True

    return _request_has_session_access(request, job)


def _get_authorized_job(request, job_id):
    try:
        job = ProcessingJob.objects.get(id=job_id)
    except ProcessingJob.DoesNotExist as exc:
        raise Http404("Job introuvable.") from exc

    if not _is_request_authorized_for_job(request, job):
        raise Http404("Job introuvable.")

    return job


class SecureProcessingJobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        job = _get_authorized_job(request, job_id)
        return Response(_serialize_job(request, job))


class SecureProcessingJobDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        job = _get_authorized_job(request, job_id)

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


class SecurePdfToImagesView(APIView):
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
                _serialize_job(request, job),
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
                    "detail": "Une erreur serveur est survenue pendant la conversion PDF vers images."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SecurePdfMergeAsyncView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist("files")

        try:
            total_size = validate_pdf_uploaded_files(
                uploaded_files=uploaded_files,
                limits=get_plan_limits(request.user),
                min_files=2,
            )
        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = ProcessingJob.objects.create(
            user=get_job_user(request.user),
            tool=ProcessingTool.PDF_MERGE,
            status=ProcessingStatus.PENDING,
            original_filename=", ".join(file.name for file in uploaded_files)[:255],
            input_size=total_size,
            options={"file_count": len(uploaded_files), "async": True},
        )

        attach_uploaded_files_to_job(job, uploaded_files)
        process_pdf_merge_job.delay(str(job.id))

        return Response(
            _serialize_job(request, job),
            status=status.HTTP_202_ACCEPTED,
        )
