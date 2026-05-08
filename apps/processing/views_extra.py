from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.converters.exceptions import ConverterError

from .pdf_extra_tools import (
    run_pdf_edit_attachments_job,
    run_pdf_ocr_job,
    run_pdf_to_zip_job,
)
from .views import _job_created_response


class PdfEditAttachmentsView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        attachment_files = request.FILES.getlist("attachments")
        remove_existing = request.data.get("remove_existing", "false")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer un PDF avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not attachment_files and str(remove_existing).strip().lower() not in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }:
            return Response(
                {
                    "detail": "Veuillez envoyer au moins un fichier joint ou activer remove_existing."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job = run_pdf_edit_attachments_job(
                user=request.user,
                uploaded_file=uploaded_file,
                attachment_files=attachment_files,
                options={"remove_existing": remove_existing},
            )

            return _job_created_response(request, job)

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la modification des pieces jointes PDF."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PdfToZipView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer un PDF avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job = run_pdf_to_zip_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options={},
            )

            return _job_created_response(request, job)

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"detail": "Une erreur serveur est survenue pendant l'export ZIP du PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PdfOcrView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer un PDF avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job = run_pdf_ocr_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options={"language": request.data.get("language", "fra+eng")},
            )

            return _job_created_response(request, job)

        except ConverterError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"detail": "Une erreur serveur est survenue pendant la preparation OCR du PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
