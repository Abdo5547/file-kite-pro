from pathlib import Path
from typing import Iterable

from django.core.files.uploadedfile import UploadedFile

from apps.processing.models import ProcessingJob, ProcessingJobFile


def attach_uploaded_files_to_job(
    job: ProcessingJob,
    uploaded_files: Iterable[UploadedFile],
) -> list[ProcessingJobFile]:
    """
    Attache plusieurs fichiers uploadés à un ProcessingJob.

    À utiliser dans les views avant de lancer une tâche Celery.
    """
    job_files: list[ProcessingJobFile] = []

    for index, uploaded_file in enumerate(uploaded_files):
        job_file = ProcessingJobFile.objects.create(
            job=job,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            size=uploaded_file.size,
            order=index,
        )
        job_files.append(job_file)

    return job_files


def get_job_input_file_paths(
    job: ProcessingJob,
    temp_dir_path: Path,
) -> list[Path]:
    """
    Copie les fichiers d'entrée du job dans un dossier temporaire
    et retourne leurs chemins locaux ordonnés.

    Important pour éviter les soucis de fichiers verrouillés sous Windows
    et pour travailler avec des chemins propres dans les converters.
    """
    temp_dir_path.mkdir(parents=True, exist_ok=True)

    input_paths: list[Path] = []

    job_files = job.input_files.all().order_by("order", "created_at")

    for job_file in job_files:
        filename = Path(job_file.original_filename).name
        destination_path = temp_dir_path / f"{job_file.order}_{filename}"

        with job_file.file.open("rb") as source_file:
            destination_path.write_bytes(source_file.read())

        input_paths.append(destination_path)

    return input_paths