import tempfile
from pathlib import Path

from apps.converters.exceptions import ConverterError, InvalidFileError
from apps.converters.images.batch_rotate import rotate_images_batch
from apps.converters.images.convert import convert_image_file
from apps.converters.images.crop import crop_image_file
from apps.plans.limits import get_plan_limits

from .models import ProcessingTool
from .services import (
    _normalize_image_output_format,
    complete_processing_job,
    create_processing_job,
    create_zip_from_files,
    fail_processing_job,
    save_single_uploaded_file_to_temp,
    save_uploaded_images_to_temp,
)
from .validators import validate_image_uploaded_files


def run_image_convert_to_jpg_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    validate_image_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    quality = int(options.get("quality", 90))
    background = options.get("background", "#ffffff")

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_CONVERT_TO_JPG,
        original_filename=uploaded_file.name,
        input_size=uploaded_file.size,
        options={
            "output_format": "jpg",
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
            output_path = temp_dir_path / "converted_image.jpg"

            convert_image_file(
                input_path=input_path,
                output_path=str(output_path),
                output_format="jpeg",
                quality=quality,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="converted_image.jpg",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la conversion vers JPG.",
        )
        raise


def run_image_convert_from_jpg_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    validate_image_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    input_extension = Path(uploaded_file.name).suffix.lower()
    if input_extension not in {".jpg", ".jpeg"}:
        raise InvalidFileError("Cet endpoint accepte uniquement des fichiers JPG ou JPEG.")

    output_format = str(options.get("output_format", "png")).lower()
    quality = int(options.get("quality", 90))
    background = options.get("background", "#ffffff")

    if output_format not in {"png", "webp"}:
        raise InvalidFileError("La conversion depuis JPG supporte actuellement png ou webp.")

    normalized_output_format, output_extension = _normalize_image_output_format(output_format)

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_CONVERT_FROM_JPG,
        original_filename=uploaded_file.name,
        input_size=uploaded_file.size,
        options={
            "output_format": output_format,
            "quality": quality,
            "background": background,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=input_extension,
            )
            output_path = temp_dir_path / f"converted_from_jpg.{output_extension}"

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
                output_filename=f"converted_from_jpg.{output_extension}",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la conversion depuis JPG.",
        )
        raise


def run_image_crop_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)

    validate_image_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    x = int(options.get("x", 0))
    y = int(options.get("y", 0))
    width = int(options.get("width"))
    height = int(options.get("height"))
    output_format = str(options.get("output_format", "webp")).lower()
    quality = int(options.get("quality", 85))
    background = options.get("background", "#ffffff")

    normalized_output_format, output_extension = _normalize_image_output_format(output_format)

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_CROP,
        original_filename=uploaded_file.name,
        input_size=uploaded_file.size,
        options={
            "x": x,
            "y": y,
            "width": width,
            "height": height,
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
            output_path = temp_dir_path / f"cropped_image.{output_extension}"

            crop_image_file(
                input_path=input_path,
                output_path=str(output_path),
                x=x,
                y=y,
                width=width,
                height=height,
                output_format=normalized_output_format,
                quality=quality,
                background=background,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename=f"cropped_image.{output_extension}",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant le recadrage image.",
        )
        raise


def run_image_rotate_batch_job(*, user, uploaded_files, options):
    limits = get_plan_limits(user)

    total_size = validate_image_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=1,
    )

    operation = str(options.get("operation", "rotate_90")).lower()
    output_format = str(options.get("output_format", "webp")).lower()
    quality = int(options.get("quality", 85))
    background = options.get("background", "#ffffff")

    normalized_output_format, _ = _normalize_image_output_format(output_format)

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.IMAGE_ROTATE_BATCH,
        original_filename=", ".join(file.name for file in uploaded_files),
        input_size=total_size,
        options={
            "operation": operation,
            "output_format": output_format,
            "quality": quality,
            "background": background,
            "file_count": len(uploaded_files),
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_paths = save_uploaded_images_to_temp(
                uploaded_files=uploaded_files,
                temp_dir_path=temp_dir_path,
            )
            output_dir = temp_dir_path / "rotated_images"

            output_paths = rotate_images_batch(
                input_paths=input_paths,
                output_dir=str(output_dir),
                operation=operation,
                output_format=normalized_output_format,
                quality=quality,
                background=background,
            )

            zip_path = temp_dir_path / "rotated_images.zip"

            create_zip_from_files(
                file_paths=output_paths,
                output_zip_path=zip_path,
            )

            return complete_processing_job(
                job,
                output_file_path=zip_path,
                output_filename="rotated_images.zip",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la rotation par lot des images.",
        )
        raise
