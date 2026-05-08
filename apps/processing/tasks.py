import tempfile
from pathlib import Path

from celery import shared_task
from django.utils import timezone

from apps.converters.exceptions import ConverterError
from apps.converters.pdf.merge import merge_pdf_files
from apps.converters.pdf.pdf_to_images import pdf_to_images_files

from .models import ProcessingJob, ProcessingStatus
from .services import (
    complete_processing_job,
    create_zip_from_files,
    fail_processing_job,
    get_job_input_file_paths,
)
from .validators import validate_pdf_file_on_disk


@shared_task
def process_pdf_to_images_job(job_id):
    try:
        job = ProcessingJob.objects.get(id=job_id)
    except ProcessingJob.DoesNotExist:
        return {"status": "FAILED", "error": "Job introuvable."}

    if not job.input_file:
        fail_processing_job(job, "Aucun fichier d'entrée disponible.")
        return {"status": "FAILED", "error": "Aucun fichier d'entrée disponible."}

    job.status = ProcessingStatus.PROCESSING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])

    try:
        output_format = job.options.get("output_format", "png")
        scale = float(job.options.get("scale", 2.0))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = temp_dir_path / "input.pdf"

            with job.input_file.open("rb") as source:
                input_path.write_bytes(source.read())

            output_dir = temp_dir_path / "pdf_images"
            image_paths = pdf_to_images_files(
                input_path=str(input_path),
                output_dir=str(output_dir),
                output_format=output_format,
                scale=scale,
            )

            zip_path = temp_dir_path / "pdf_images.zip"
            create_zip_from_files(
                file_paths=image_paths,
                output_zip_path=zip_path,
            )

            complete_processing_job(
                job,
                output_file_path=zip_path,
                output_filename="pdf_images.zip",
            )

        return {"status": "COMPLETED", "job_id": str(job.id)}

    except ConverterError as exc:
        fail_processing_job(job, exc)
        return {"status": "FAILED", "error": str(exc)}

    except Exception as exc:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la conversion PDF vers images.",
        )
        return {"status": "FAILED", "error": str(exc)}


@shared_task
def process_pdf_merge_job(job_id):
    try:
        job = ProcessingJob.objects.get(id=job_id)
    except ProcessingJob.DoesNotExist:
        return {"status": "FAILED", "error": "Job introuvable."}

    job.status = ProcessingStatus.PROCESSING
    if hasattr(job, "started_at"):
        job.started_at = timezone.now()

    update_fields = ["status"]
    if hasattr(job, "started_at"):
        update_fields.append("started_at")
    if hasattr(job, "updated_at"):
        update_fields.append("updated_at")
    job.save(update_fields=update_fields)

    if job.input_files.count() < 2:
        message = "Au moins deux fichiers PDF sont requis pour la fusion."
        fail_processing_job(job, message)
        return {
            "status": "FAILED",
            "job_id": str(job.id),
            "error": message,
        }

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_paths = get_job_input_file_paths(job, temp_dir_path)

            for input_path in input_paths:
                validate_pdf_file_on_disk(input_path)

            output_path = temp_dir_path / f"merged_{job.id}.pdf"
            merge_pdf_files(
                input_paths=[str(path) for path in input_paths],
                output_path=output_path,
            )

            if not output_path.exists():
                raise RuntimeError("PDF merge failed: output file was not created.")

            complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename=f"merged_{job.id}.pdf",
            )

        return {
            "status": "COMPLETED",
            "job_id": str(job.id),
        }

    except ConverterError as exc:
        fail_processing_job(job, exc)
        return {
            "status": "FAILED",
            "job_id": str(job.id),
            "error": str(exc),
        }

    except Exception as exc:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la fusion PDF.",
        )
        return {
            "status": "FAILED",
            "job_id": str(job.id),
            "error": str(exc),
        }
