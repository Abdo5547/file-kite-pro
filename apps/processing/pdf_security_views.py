from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.converters.exceptions import ConverterError

from .models import ProcessingTool
from .pdf_security_services import (
    run_change_permissions_pdf_job,
    run_decrypt_pdf_job,
    run_encrypt_pdf_job,
    run_flatten_pdf_job,
    run_find_and_redact_pdf_job,
    run_remove_metadata_pdf_job,
    run_sanitize_pdf_job,
)
from .serializers import ProcessingJobSerializer


class EncryptPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        options = {
            "user_password": request.data.get("user_password", ""),
            "owner_password": request.data.get("owner_password", ""),
            "algorithm": request.data.get("algorithm", "AES-256"),
        }

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_encrypt_pdf_job,
            options=options,
            generic_error="Une erreur serveur est survenue pendant le chiffrement PDF.",
        )


class DecryptPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        options = {"password": request.data.get("password", "")}

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_decrypt_pdf_job,
            options=options,
            generic_error="Une erreur serveur est survenue pendant le dechiffrement PDF.",
        )


class RemoveRestrictionsPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        options = {"password": request.data.get("password", "")}

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=lambda **kwargs: run_decrypt_pdf_job(tool=ProcessingTool.PDF_REMOVE_RESTRICTIONS, **kwargs),
            options=options,
            generic_error="Une erreur serveur est survenue pendant la suppression des restrictions PDF.",
        )


class SanitizePdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        options = {"password": request.data.get("password", "")}

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_sanitize_pdf_job,
            options=options,
            generic_error="Une erreur serveur est survenue pendant le nettoyage du PDF.",
        )


class RemoveMetadataPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        options = {"password": request.data.get("password", "")}

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_remove_metadata_pdf_job,
            options=options,
            generic_error="Une erreur serveur est survenue pendant la suppression des metadonnees.",
        )


class ChangePermissionsPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        raw_permissions = request.data.getlist("allowed_permissions")
        if not raw_permissions:
            raw_value = request.data.get("allowed_permissions", "")
            raw_permissions = [item.strip() for item in str(raw_value).split(",") if item.strip()]

        options = {
            "user_password": request.data.get("user_password", ""),
            "owner_password": request.data.get("owner_password", ""),
            "source_password": request.data.get("source_password", ""),
            "algorithm": request.data.get("algorithm", "AES-256"),
            "allowed_permissions": raw_permissions,
        }

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_change_permissions_pdf_job,
            options=options,
            generic_error="Une erreur serveur est survenue pendant la modification des permissions PDF.",
        )


class FindAndRedactPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        options = {
            "search_text": request.data.get("search_text", ""),
            "replacement_text": request.data.get("replacement_text", ""),
        }

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_find_and_redact_pdf_job,
            options=options,
            generic_error="Une erreur serveur est survenue pendant le masquage du texte PDF.",
        )


class FlattenPdfView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Veuillez envoyer un PDF avec le champ 'file'."}, status=status.HTTP_400_BAD_REQUEST)

        return _run_single_file_job(
            request=request,
            uploaded_file=uploaded_file,
            runner=run_flatten_pdf_job,
            options={},
            generic_error="Une erreur serveur est survenue pendant l'aplatissement du PDF.",
        )


def _run_single_file_job(*, request, uploaded_file, runner, options, generic_error):
    try:
        job = runner(
            user=request.user,
            uploaded_file=uploaded_file,
            options=options,
        )

        return Response(
            ProcessingJobSerializer(job, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    except ConverterError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"detail": generic_error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
