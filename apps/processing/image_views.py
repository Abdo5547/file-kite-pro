from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.converters.exceptions import ConverterError

from .image_services import (
    run_image_convert_from_jpg_job,
    run_image_convert_to_jpg_job,
    run_image_crop_job,
    run_image_rotate_batch_job,
)
from .serializers import ProcessingJobSerializer


class ImageConvertToJpgView(APIView):
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
            "quality": request.data.get("quality", 90),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_convert_to_jpg_job(
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
            return Response(
                {"detail": "Une erreur serveur est survenue pendant la conversion vers JPG."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImageConvertFromJpgView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "Veuillez envoyer une image JPG avec le champ 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        options = {
            "output_format": request.data.get("output_format", "png"),
            "quality": request.data.get("quality", 90),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_convert_from_jpg_job(
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
            return Response(
                {"detail": "Une erreur serveur est survenue pendant la conversion depuis JPG."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImageCropView(APIView):
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
            "x": request.data.get("x", 0),
            "y": request.data.get("y", 0),
            "width": request.data.get("width"),
            "height": request.data.get("height"),
            "output_format": request.data.get("output_format", "webp"),
            "quality": request.data.get("quality", 85),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_crop_job(
                user=request.user,
                uploaded_file=uploaded_file,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except (TypeError, ValueError):
            return Response(
                {"detail": "Les coordonnees et dimensions du recadrage sont invalides."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ConverterError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"detail": "Une erreur serveur est survenue pendant le recadrage image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImageRotateBatchView(APIView):
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
            "operation": request.data.get("operation", "rotate_90"),
            "output_format": request.data.get("output_format", "webp"),
            "quality": request.data.get("quality", 85),
            "background": request.data.get("background", "#ffffff"),
        }

        try:
            job = run_image_rotate_batch_job(
                user=request.user,
                uploaded_files=uploaded_files,
                options=options,
            )

            return Response(
                ProcessingJobSerializer(job, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ConverterError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {
                    "detail": "Une erreur serveur est survenue pendant la rotation par lot des images."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
