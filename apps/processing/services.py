import tempfile
from pathlib import Path

from django.core.files import File
from django.utils import timezone

from apps.converters.exceptions import ConverterError



from apps.converters.pdf.merge import merge_pdf_files

from apps.plans.limits import get_plan_limits

from .models import ProcessingJob, ProcessingStatus, ProcessingTool
from .validators import validate_pdf_file_on_disk, validate_pdf_uploaded_files , validate_image_uploaded_files

from apps.converters.images.convert import convert_image_file

from apps.converters.images.resize import resize_image_file
from apps.converters.images.compress import compress_image_file
from apps.converters.images.rotate import rotate_flip_image_file



from apps.converters.pdf.images_to_pdf import images_to_pdf_file


import zipfile
from apps.converters.pdf.split import parse_pages_expression, split_pdf_file

from django.core.files.base import ContentFile

from apps.converters.exceptions import ConverterError, InvalidFileError

from apps.converters.pdf.pdf_to_images import pdf_to_images_files

from apps.converters.pdf.rotate import rotate_pdf_file

from pathlib import Path
from typing import Iterable

from django.core.files.uploadedfile import UploadedFile

from apps.processing.models import ProcessingJob, ProcessingJobFile




def enqueue_pdf_to_images_job(*, user, uploaded_file, options):
    from .tasks import process_pdf_to_images_job

    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_pdf_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    output_format = str(options.get("output_format", "png")).lower()
    scale = float(options.get("scale", 2.0))

    if output_format == "jpeg":
        output_format = "jpg"

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_TO_IMAGES,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "output_format": output_format,
            "scale": scale,
            "async": True,
        },
    )

    job.status = ProcessingStatus.PENDING
    attach_uploaded_file_to_job(job, uploaded_file)
    job.save(update_fields=["status", "updated_at"])

    process_pdf_to_images_job.delay(str(job.id))

    return job


def attach_uploaded_file_to_job(job, uploaded_file):
    uploaded_file.seek(0)

    filename = uploaded_file.name

    job.input_file.save(
        filename,
        ContentFile(uploaded_file.read()),
        save=False,
    )

    job.save(update_fields=["input_file", "updated_at"])

    uploaded_file.seek(0)

    return job


def get_job_user(user):
    if user and user.is_authenticated:
        return user
    return None


def create_processing_job(
    *,
    user,
    tool,
    original_filename="",
    input_size=0,
    options=None,
):
    return ProcessingJob.objects.create(
        user=get_job_user(user),
        tool=tool,
        status=ProcessingStatus.PROCESSING,
        original_filename=original_filename[:255],
        input_size=input_size,
        options=options or {},
        started_at=timezone.now(),
    )


def complete_processing_job(job, *, output_file_path, output_filename):
    output_file_path = Path(output_file_path)

    with output_file_path.open("rb") as output_file:
        job.output_file.save(
            output_filename,
            File(output_file),
            save=False,
        )

    job.status = ProcessingStatus.COMPLETED
    job.output_size = output_file_path.stat().st_size
    job.completed_at = timezone.now()
    job.save()

    return job


def fail_processing_job(job, error_message):
    job.status = ProcessingStatus.FAILED
    job.error_message = str(error_message)
    job.completed_at = timezone.now()
    job.save()

    return job


def save_uploaded_files_to_temp(uploaded_files, temp_dir_path):
    input_paths = []

    for index, uploaded_file in enumerate(uploaded_files, start=1):
        safe_path = temp_dir_path / f"input_{index}.pdf"

        with safe_path.open("wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        input_paths.append(str(safe_path))

    return input_paths


def run_pdf_merge_job(*, user, uploaded_files):
    limits = get_plan_limits(user)

    total_size = validate_pdf_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=2,
    )

    original_filename = ", ".join([file.name for file in uploaded_files])

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_MERGE,
        original_filename=original_filename,
        input_size=total_size,
        options={
            "file_count": len(uploaded_files),
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_paths = save_uploaded_files_to_temp(
                uploaded_files=uploaded_files,
                temp_dir_path=temp_dir_path,
            )

            for input_path in input_paths:
                validate_pdf_file_on_disk(input_path)

            output_path = temp_dir_path / "merged_document.pdf"

            merge_pdf_files(
                input_paths=input_paths,
                output_path=str(output_path),
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="merged_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception as exc:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant le traitement PDF.",
        )
        raise


def save_single_uploaded_file_to_temp(uploaded_file, temp_dir_path, suffix):
    safe_path = temp_dir_path / f"input{suffix}"

    with safe_path.open("wb") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return str(safe_path)


def run_image_convert_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_image_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    output_format = str(options.get("output_format", "webp")).lower()
    quality = int(options.get("quality", 85))
    background = options.get("background", "#ffffff")

    if output_format == "jpg":
        normalized_output_format = "jpeg"
    else:
        normalized_output_format = output_format

    output_extension = "jpg" if normalized_output_format == "jpeg" else normalized_output_format

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_CONVERT,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "output_format": output_format,
            "quality": quality,
            "background": background,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_suffix = Path(uploaded_file.name).suffix.lower() or ".img"

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_suffix,
            )

            output_path = temp_dir_path / f"converted_image.{output_extension}"

            convert_image_file(
                input_path=input_path,
                output_path=str(output_path),
                output_format=normalized_output_format,
                quality=quality,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename=f"converted_image.{output_extension}",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la conversion image.",
        )
        raise


def run_image_resize_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_image_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    width = options.get("width")
    height = options.get("height")

    width = int(width) if width not in (None, "", "null") else None
    height = int(height) if height not in (None, "", "null") else None

    keep_ratio = str(options.get("keep_ratio", "true")).lower() in {
        "true",
        "1",
        "yes",
    }

    output_format = str(options.get("output_format", "webp")).lower()
    quality = int(options.get("quality", 85))
    background = options.get("background", "#ffffff")

    normalized_output_format = "jpeg" if output_format == "jpg" else output_format
    output_extension = "jpg" if normalized_output_format == "jpeg" else normalized_output_format

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_RESIZE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "width": width,
            "height": height,
            "keep_ratio": keep_ratio,
            "output_format": output_format,
            "quality": quality,
            "background": background,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_suffix = Path(uploaded_file.name).suffix.lower() or ".img"

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_suffix,
            )

            output_path = temp_dir_path / f"resized_image.{output_extension}"

            resize_image_file(
                input_path=input_path,
                output_path=str(output_path),
                width=width,
                height=height,
                keep_ratio=keep_ratio,
                output_format=normalized_output_format,
                quality=quality,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename=f"resized_image.{output_extension}",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant le redimensionnement image.",
        )
        raise


def run_image_compress_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_image_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    output_format = str(options.get("output_format", "webp")).lower()
    quality = int(options.get("quality", 75))
    background = options.get("background", "#ffffff")

    normalized_output_format = "jpeg" if output_format == "jpg" else output_format
    output_extension = "jpg" if normalized_output_format == "jpeg" else normalized_output_format

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_COMPRESS,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "output_format": output_format,
            "quality": quality,
            "background": background,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_suffix = Path(uploaded_file.name).suffix.lower() or ".img"

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_suffix,
            )

            output_path = temp_dir_path / f"compressed_image.{output_extension}"

            compress_image_file(
                input_path=input_path,
                output_path=str(output_path),
                output_format=normalized_output_format,
                quality=quality,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename=f"compressed_image.{output_extension}",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la compression image.",
        )
        raise


def run_image_rotate_flip_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_image_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    operation = str(options.get("operation", "rotate_90")).lower()
    output_format = str(options.get("output_format", "webp")).lower()
    quality = int(options.get("quality", 85))
    background = options.get("background", "#ffffff")

    normalized_output_format = "jpeg" if output_format == "jpg" else output_format
    output_extension = "jpg" if normalized_output_format == "jpeg" else normalized_output_format

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_ROTATE_FLIP,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "operation": operation,
            "output_format": output_format,
            "quality": quality,
            "background": background,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_suffix = Path(uploaded_file.name).suffix.lower() or ".img"

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_suffix,
            )

            output_path = temp_dir_path / f"transformed_image.{output_extension}"

            rotate_flip_image_file(
                input_path=input_path,
                output_path=str(output_path),
                operation=operation,
                output_format=normalized_output_format,
                quality=quality,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename=f"transformed_image.{output_extension}",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la rotation ou le flip image.",
        )
        raise


def save_uploaded_images_to_temp(uploaded_files, temp_dir_path):
    input_paths = []

    for index, uploaded_file in enumerate(uploaded_files, start=1):
        suffix = Path(uploaded_file.name).suffix.lower() or ".img"
        safe_path = temp_dir_path / f"image_{index}{suffix}"

        with safe_path.open("wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        input_paths.append(str(safe_path))

    return input_paths


def run_images_to_pdf_job(*, user, uploaded_files, options):
    limits = get_plan_limits(user)

    total_size = validate_image_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    page_size = str(options.get("page_size", "auto")).lower()
    orientation = str(options.get("orientation", "portrait")).lower()
    background = options.get("background", "#ffffff")

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGES_TO_PDF,
        original_filename=", ".join([file.name for file in uploaded_files]),
        input_size=total_size,
        options={
            "file_count": len(uploaded_files),
            "page_size": page_size,
            "orientation": orientation,
            "background": background,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_paths = save_uploaded_images_to_temp(
                uploaded_files=uploaded_files,
                temp_dir_path=temp_dir_path,
            )

            output_path = temp_dir_path / "images_document.pdf"

            images_to_pdf_file(
                input_paths=input_paths,
                output_path=str(output_path),
                page_size=page_size,
                orientation=orientation,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="images_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la conversion images vers PDF.",
        )
        raise


def create_zip_from_files(*, file_paths, output_zip_path):
    output_zip_path = Path(output_zip_path)
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            file_path = Path(file_path)
            zip_file.write(file_path, arcname=file_path.name)

    return str(output_zip_path)


def run_pdf_split_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_pdf_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    mode = str(options.get("mode", "all")).lower()
    pages_expression = str(options.get("pages", "")).strip()

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_SPLIT,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "mode": mode,
            "pages": pages_expression,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_suffix = Path(uploaded_file.name).suffix.lower() or ".pdf"

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_suffix,
            )

            validate_pdf_file_on_disk(input_path)

            pages = None

            if mode == "selected":
                pages = parse_pages_expression(pages_expression)
            elif mode != "all":
                raise InvalidFileError("Mode de division PDF non supporté.")

            split_output_dir = temp_dir_path / "split_pages"

            split_files = split_pdf_file(
                input_path=input_path,
                output_dir=str(split_output_dir),
                pages=pages,
            )

            zip_path = temp_dir_path / "split_pages.zip"

            create_zip_from_files(
                file_paths=split_files,
                output_zip_path=zip_path,
            )

            return complete_processing_job(
                job,
                output_file_path=zip_path,
                output_filename="split_pages.zip",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la division PDF.",
        )
        raise


def run_pdf_rotate_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_pdf_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    angle = int(options.get("angle", 90))
    pages = str(options.get("pages", "all")).strip() or "all"

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_ROTATE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "angle": angle,
            "pages": pages,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_suffix = Path(uploaded_file.name).suffix.lower() or ".pdf"

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_suffix,
            )

            validate_pdf_file_on_disk(input_path)

            output_path = temp_dir_path / "rotated_document.pdf"

            rotate_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                angle=angle,
                pages_expression=pages,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="rotated_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la rotation PDF.",
        )
        raise


def run_pdf_to_images_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    uploaded_files = [uploaded_file]

    total_size = validate_pdf_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    output_format = str(options.get("output_format", "png")).lower()
    scale = float(options.get("scale", 2.0))

    if output_format == "jpeg":
        output_format = "jpg"

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_TO_IMAGES,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "output_format": output_format,
            "scale": scale,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=".pdf",
            )

   

            output_dir = temp_dir_path / "pdf_images"

            image_paths = pdf_to_images_files(
                input_path=input_path,
                output_dir=str(output_dir),
                output_format=output_format,
                scale=scale,
            )

            zip_path = temp_dir_path / "pdf_images.zip"

            create_zip_from_files(
                file_paths=image_paths,
                output_zip_path=zip_path,
            )

            return complete_processing_job(
                job,
                output_file_path=zip_path,
                output_filename="pdf_images.zip",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise

    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la conversion PDF vers images.",
        )
        raise





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




















