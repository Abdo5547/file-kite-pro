import tempfile
from pathlib import Path

from apps.converters.exceptions import ConverterError, InvalidFileError
from apps.converters.pdf.add_blank_page import add_blank_page_to_pdf_file
from apps.converters.pdf.alternate_merge import alternate_merge_pdf_files
from apps.converters.pdf.combine_single_page import combine_pdf_into_single_page_file
from apps.converters.pdf.delete_pages import delete_pdf_pages_file
from apps.converters.pdf.divide_pages import divide_pdf_pages_file
from apps.converters.pdf.extract_pages import extract_pdf_pages_file
from apps.converters.pdf.grid_combine import grid_combine_pdf_file, n_up_pdf_file
from apps.converters.pdf.organize import organize_pdf_file
from apps.converters.pdf.posterize_pdf import posterize_pdf_file
from apps.converters.pdf.reverse_pages import reverse_pdf_pages_file
from apps.converters.pdf.rotate_custom import rotate_custom_pdf_file
from apps.plans.limits import get_plan_limits

from .models import ProcessingTool
from .services import (
    complete_processing_job,
    create_processing_job,
    fail_processing_job,
    save_single_uploaded_file_to_temp,
    save_uploaded_files_to_temp,
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


def run_pdf_rotate_custom_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    rotations_expression = str(options.get("rotations", "")).strip()

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_ROTATE_CUSTOM,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"rotations": rotations_expression},
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

            output_path = temp_dir_path / "custom_rotated.pdf"
            rotate_custom_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                rotations_expression=rotations_expression,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="custom_rotated.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la rotation personnalisee PDF.",
        )
        raise


def run_pdf_add_blank_page_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    position = str(options.get("position", "after")).strip().lower()
    page_number_raw = options.get("page")
    width_raw = options.get("width")
    height_raw = options.get("height")

    page_number = None
    if page_number_raw not in (None, "", "null"):
        try:
            page_number = int(page_number_raw)
        except (TypeError, ValueError) as exc:
            raise InvalidFileError("Le numero de page doit etre un entier.") from exc

    width = float(width_raw) if width_raw not in (None, "", "null") else None
    height = float(height_raw) if height_raw not in (None, "", "null") else None

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_ADD_BLANK_PAGE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={
            "position": position,
            "page": page_number,
            "width": width,
            "height": height,
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

            output_path = temp_dir_path / "blank_page_added.pdf"
            add_blank_page_to_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                position=position,
                page_number=page_number,
                width=width,
                height=height,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="blank_page_added.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant l'ajout d'une page blanche.",
        )
        raise


def run_pdf_reverse_pages_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_REVERSE_PAGES,
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

            output_path = temp_dir_path / "reversed_document.pdf"
            reverse_pdf_pages_file(
                input_path=input_path,
                output_path=str(output_path),
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="reversed_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant l'inversion des pages PDF.",
        )
        raise


def run_pdf_n_up_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    pages_per_sheet_raw = options.get("pages_per_sheet", 4)
    try:
        pages_per_sheet = int(pages_per_sheet_raw)
    except (TypeError, ValueError) as exc:
        raise InvalidFileError("Le nombre de pages par feuille doit etre un entier.") from exc

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_N_UP,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"pages_per_sheet": pages_per_sheet},
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

            output_path = temp_dir_path / "n_up_document.pdf"
            n_up_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                pages_per_sheet=pages_per_sheet,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="n_up_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la composition n-up PDF.",
        )
        raise


def run_pdf_grid_combine_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    try:
        rows = int(options.get("rows", 2))
        columns = int(options.get("columns", 2))
    except (TypeError, ValueError) as exc:
        raise InvalidFileError("Les dimensions de grille doivent etre des entiers.") from exc

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_GRID_COMBINE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"rows": rows, "columns": columns},
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

            output_path = temp_dir_path / "grid_combined_document.pdf"
            grid_combine_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                rows=rows,
                columns=columns,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="grid_combined_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la combinaison en grille PDF.",
        )
        raise


def run_pdf_alternate_merge_job(*, user, uploaded_files, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=uploaded_files,
        limits=limits,
        min_files=2,
    )

    if len(uploaded_files) != 2:
        raise InvalidFileError("Veuillez envoyer exactement deux fichiers PDF.")

    original_filename = ", ".join(file.name for file in uploaded_files)

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_ALTERNATE_MERGE,
        original_filename=original_filename,
        input_size=total_size,
        options={"file_count": len(uploaded_files)},
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

            output_path = temp_dir_path / "alternate_merged_document.pdf"
            alternate_merge_pdf_files(
                input_paths=input_paths,
                output_path=str(output_path),
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="alternate_merged_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la fusion alternee PDF.",
        )
        raise


def run_pdf_divide_pages_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    mode = str(options.get("mode", "vertical")).strip().lower()

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_DIVIDE_PAGES,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"mode": mode},
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

            output_path = temp_dir_path / "divided_pages.pdf"
            divide_pdf_pages_file(
                input_path=input_path,
                output_path=str(output_path),
                mode=mode,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="divided_pages.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la division des pages PDF.",
        )
        raise


def run_pdf_combine_single_page_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    gap_raw = options.get("gap", 0)
    try:
        gap = float(gap_raw)
    except (TypeError, ValueError) as exc:
        raise InvalidFileError("L'espacement doit etre numerique.") from exc

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_COMBINE_SINGLE_PAGE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"gap": gap},
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

            output_path = temp_dir_path / "single_page_document.pdf"
            combine_pdf_into_single_page_file(
                input_path=input_path,
                output_path=str(output_path),
                gap=gap,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="single_page_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la combinaison sur une seule page.",
        )
        raise


def run_pdf_posterize_job(*, user, uploaded_file, options):
    limits = get_plan_limits(user)
    total_size = validate_pdf_uploaded_files(
        uploaded_files=[uploaded_file],
        limits=limits,
        min_files=1,
    )

    try:
        rows = int(options.get("rows", 2))
        columns = int(options.get("columns", 2))
    except (TypeError, ValueError) as exc:
        raise InvalidFileError("Les dimensions du poster doivent etre des entiers.") from exc

    job = create_processing_job(
        user=user,
        tool=ProcessingTool.PDF_POSTERIZE,
        original_filename=uploaded_file.name,
        input_size=total_size,
        options={"rows": rows, "columns": columns},
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

            output_path = temp_dir_path / "posterized_document.pdf"
            posterize_pdf_file(
                input_path=input_path,
                output_path=str(output_path),
                rows=rows,
                columns=columns,
            )

            return complete_processing_job(
                job,
                output_file_path=output_path,
                output_filename="posterized_document.pdf",
            )

    except ConverterError as exc:
        fail_processing_job(job, exc)
        raise
    except Exception:
        fail_processing_job(
            job,
            "Une erreur inattendue est survenue pendant la posterisation PDF.",
        )
        raise
