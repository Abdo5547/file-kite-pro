import tempfile
from pathlib import Path

from apps.converters.exceptions import ConverterError
from apps.converters.pdf.delete_pages import delete_pdf_pages_file
from apps.converters.pdf.extract_pages import extract_pdf_pages_file
from apps.converters.pdf.organize import organize_pdf_file
from apps.plans.limits import get_plan_limits

from .models import ProcessingTool
from .services import (
    complete_processing_job,
    create_processing_job,
    fail_processing_job,
    save_single_uploaded_file_to_temp,
)
from .validators import validate_pdf_file_on_disk, validate_pdf_uploaded_files


def run_pdf_delete_pages_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    pages_expression = str(options.get("pages", "")).strip()

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_DELETE_PAGES,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"pages": pages_expression},
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

            output_path = temp_dir_path / "pages_deleted.pdf"
            delete_pdf_pages_file(
                input_path=input_path,
                output_path=str(output_path),
                pages_expression=pages_expression,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="pages_deleted.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la suppression de pages PDF.",
        )
        raise


def run_pdf_extract_pages_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    pages_expression = str(options.get("pages", "")).strip()

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_EXTRACT_PAGES,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"pages": pages_expression},
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

            output_path = temp_dir_path / "pages_extracted.pdf"
            extract_pdf_pages_file(
                input_path=input_path,
                output_path=str(output_path),
                pages_expression=pages_expression,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="pages_extracted.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant l'extraction de pages PDF.",
        )
        raise


def run_pdf_organize_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    pages_expression = str(options.get("pages", "")).strip()

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_ORGANIZE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"pages": pages_expression},
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

            output_path = temp_dir_path / "organized_document.pdf"
            organize_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                page_order_expression=pages_expression,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="organized_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la reorganisation PDF.",
        )
        raise
