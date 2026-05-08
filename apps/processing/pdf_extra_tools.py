import tempfile
from pathlib import Path

from apps.converters.exceptions import ConverterError, InvalidFileError
from apps.converters.pdf.edit_attachments import edit_pdf_attachments_file
from apps.converters.pdf.ocr_pdf import ocr_pdf_file
from apps.converters.pdf.pdf_to_zip import export_pdf_to_zip_file
from apps.plans.limits import get_plan_limits

from .models import ProcessingTool
from .pdf_page_tools import _save_uploaded_attachments_to_temp
from .services import (
    complete_processing_job,
    create_processing_job,
    fail_processing_job,
    save_single_uploaded_file_to_temp,
)
from .validators import (
    validate_pdf_file_on_disk,
    validate_pdf_uploaded_files,
    validate_uploaded_files,
)


def _parse_bool(value, *, default=False):
    if value in (None, "", "null"):
        return default

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def run_pdf_edit_attachments_job(*, user, uploaded_file, attachment_files, options):
    limits = get_plan_limits(user)
    attachment_files = list(attachment_files or [])
    remove_existing = _parse_bool((options or {}).get("remove_existing"), default=False)

    if not remove_existing and not attachment_files:
        raise InvalidFileError(
            "Veuillez envoyer au moins un fichier joint ou activer remove_existing."
        )

    total_size = validate_uploaded_files([uploaded_file, *attachment_files], limits)
    validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_EDIT_ATTACHMENTS,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "attachment_count": len(attachment_files),
            "remove_existing": remove_existing,
        },
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=Path(uploaded_file.name).suffix.lower() or ".pdf",
            )
            validate_pdf_file_on_disk(input_path)

            attachment_paths = _save_uploaded_attachments_to_temp(
                uploaded_files=attachment_files,
                temp_dir_path=temp_dir_path,
            )

            output_path = temp_dir_path / "attachments_edited.pdf"
            edit_pdf_attachments_file(
                input_path=input_path,
                output_path=str(output_path),
                attachment_paths=attachment_paths,
                remove_existing=remove_existing,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="attachments_edited.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la modification des pieces jointes PDF.",
        )
        raise


def run_pdf_to_zip_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_TO_ZIP,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options=options or {},
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=Path(uploaded_file.name).suffix.lower() or ".pdf",
            )
            validate_pdf_file_on_disk(input_path)

            output_path = temp_dir_path / "pdf_export.zip"
            export_pdf_to_zip_file(
                input_path=input_path,
                output_zip_path=str(output_path),
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="pdf_export.zip",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant l'export ZIP du PDF.",
        )
        raise


def run_pdf_ocr_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    language = str((options or {}).get("language", "fra+eng")).strip() or "fra+eng"

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_OCR,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"language": language},
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=Path(uploaded_file.name).suffix.lower() or ".pdf",
            )
            validate_pdf_file_on_disk(input_path)

            output_path = temp_dir_path / "ocr_prepared.pdf"
            ocr_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                language=language,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="ocr_prepared.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la preparation OCR du PDF.",
        )
        raise
