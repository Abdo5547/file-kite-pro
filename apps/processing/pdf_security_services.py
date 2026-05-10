import tempfile
from pathlib import Path

from apps.converters.exceptions import ConverterError
from apps.converters.pdf.decrypt import decrypt_pdf_file
from apps.converters.pdf.encrypt import encrypt_pdf_file
from apps.converters.pdf.metadata import remove_pdf_metadata
from apps.converters.pdf.permissions import change_pdf_permissions
from apps.converters.pdf.redact import find_and_redact_text_in_pdf
from apps.converters.pdf.sanitize import sanitize_pdf_file

from .models import ProcessingTool
from .services import (
    complete_processing_job,
    create_processing_job,
    fail_processing_job,
    save_single_uploaded_file_to_temp,
)
from .validators import validate_pdf_uploaded_files
from apps.plans.limits import get_plan_limits


def _create_single_pdf_job(*, user, uploaded_file, tool, options):
    limits = get_plan_limits(user)
    validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    return create_processing_job(
        user=user,
        tool=tool,
        original_filename=uploaded_file.name,
        input_size=uploaded_file.size,
        options=options,
    )


def run_encrypt_pdf_job(*, user, uploaded_file, options):
    user_password = str(options.get("user_password", ""))
    owner_password = str(options.get("owner_password", "")) or None
    algorithm = str(options.get("algorithm", "AES-256"))

    job = _create_single_pdf_job(
        user=user,
        uploaded_file=uploaded_file,
        tool=ProcessingTool.PDF_ENCRYPT,
        options={
            "algorithm": algorithm,
            "has_owner_password": bool(owner_password),
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
            output_path = temp_dir_path / "encrypted_document.pdf"

            encrypt_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                user_password=user_password,
                owner_password=owner_password,
                algorithm=algorithm,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="encrypted_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(job, "Une erreur inattendue est survenue pendant le chiffrement PDF.")
        raise


def run_decrypt_pdf_job(*, user, uploaded_file, options, tool=ProcessingTool.PDF_DECRYPT):
    password = str(options.get("password", ""))

    job = _create_single_pdf_job(
        user=user,
        uploaded_file=uploaded_file,
        tool=tool,
        options={},
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=".pdf",
            )
            output_path = temp_dir_path / "decrypted_document.pdf"

            decrypt_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                password=password,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="decrypted_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(job, "Une erreur inattendue est survenue pendant le dechiffrement PDF.")
        raise


def run_remove_metadata_pdf_job(*, user, uploaded_file, options):
    password = str(options.get("password", "")) or None

    job = _create_single_pdf_job(
        user=user,
        uploaded_file=uploaded_file,
        tool=ProcessingTool.PDF_REMOVE_METADATA,
        options={},
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = save_single_uploaded_file_to_temp(
                uploaded_file=uploaded_file,
                temp_dir_path=temp_dir_path,
                suffix=".pdf",
            )
            output_path = temp_dir_path / "metadata_removed.pdf"

            remove_pdf_metadata(
                input_path=input_path,
                output_path=str(output_path),
                password=password,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="metadata_removed.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(job, "Une erreur inattendue est survenue pendant la suppression des metadonnees.")
        raise


def run_sanitize_pdf_job(*, user, uploaded_file, options):
    password = str(options.get("password", "")) or None

    job = _create_single_pdf_job(
        user=user,
        uploaded_file=uploaded_file,
        tool=ProcessingTool.PDF_SANITIZE,
        options={
            "remove_links": True,
            "remove_file_attachments": True,
            "remove_javascript": True,
            "remove_metadata": True,
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
            output_path = temp_dir_path / "sanitized_document.pdf"

            sanitize_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                password=password,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="sanitized_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(job, "Une erreur inattendue est survenue pendant le nettoyage du PDF.")
        raise


def run_change_permissions_pdf_job(*, user, uploaded_file, options):
    job = _create_single_pdf_job(
        user=user,
        uploaded_file=uploaded_file,
        tool=ProcessingTool.PDF_CHANGE_PERMISSIONS,
        options={
            "allowed_permissions": options.get("allowed_permissions", []),
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
            output_path = temp_dir_path / "permissions_updated.pdf"

            change_pdf_permissions(
                input_path=input_path,
                output_path=str(output_path),
                user_password=str(options.get("user_password", "")),
                owner_password=str(options.get("owner_password", "")),
                source_password=str(options.get("source_password", "")) or None,
                allowed_permissions=list(options.get("allowed_permissions", [])),
                algorithm=str(options.get("algorithm", "AES-256")),
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="permissions_updated.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(job, "Une erreur inattendue est survenue pendant la modification des permissions PDF.")
        raise


def run_find_and_redact_pdf_job(*, user, uploaded_file, options):
    search_text = str(options.get("search_text", ""))
    replacement_text = str(options.get("replacement_text", ""))

    job = _create_single_pdf_job(
        user=user,
        uploaded_file=uploaded_file,
        tool=ProcessingTool.PDF_FIND_AND_REDACT,
        options={
            "search_text": search_text,
            "replacement_text": replacement_text,
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
            output_path = temp_dir_path / "redacted_document.pdf"

            find_and_redact_text_in_pdf(
                input_path=input_path,
                output_path=str(output_path),
                search_text=search_text,
                replacement_text=replacement_text,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="redacted_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(job, "Une erreur inattendue est survenue pendant le masquage du texte PDF.")
        raise
