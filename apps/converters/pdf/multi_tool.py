import tempfile
from pathlib import Path

from apps.converters.exceptions import InvalidFileError, ProtectedFileError
from apps.converters.pdf.add_attachments import add_attachments_to_pdf_file
from apps.converters.pdf.add_blank_page import add_blank_page_to_pdf_file
from apps.converters.pdf.combine_single_page import combine_pdf_into_single_page_file
from apps.converters.pdf.delete_pages import delete_pdf_pages_file
from apps.converters.pdf.divide_pages import divide_pdf_pages_file
from apps.converters.pdf.extract_pages import extract_pdf_pages_file
from apps.converters.pdf.grid_combine import grid_combine_pdf_file, n_up_pdf_file
from apps.converters.pdf.organize import organize_pdf_file
from apps.converters.pdf.posterize_pdf import posterize_pdf_file
from apps.converters.pdf.reverse_pages import reverse_pdf_pages_file
from apps.converters.pdf.rotate import rotate_pdf_file
from apps.converters.pdf.rotate_custom import rotate_custom_pdf_file


ALIASES = {
    "delete-pages": "delete-pages",
    "pdf-delete-pages": "delete-pages",
    "extract-pages": "extract-pages",
    "pdf-extract-pages": "extract-pages",
    "organize-pdf": "organize-pdf",
    "organize": "organize-pdf",
    "rotate-pdf": "rotate-pdf",
    "pdf-rotate": "rotate-pdf",
    "rotate-custom": "rotate-custom",
    "add-blank-page": "add-blank-page",
    "reverse-pages": "reverse-pages",
    "n-up-pdf": "n-up-pdf",
    "n-up": "n-up-pdf",
    "grid-combine": "grid-combine",
    "divide-pages": "divide-pages",
    "combine-single-page": "combine-single-page",
    "posterize-pdf": "posterize-pdf",
    "posterize": "posterize-pdf",
    "add-attachments": "add-attachments",
}


def run_pdf_multi_tool_file(
    *,
    input_path: str,
    output_path: str,
    operations: list[dict],
    attachment_paths: list[str] | None = None,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    normalized_operations = _validate_operations(operations)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            current_input = input_path

            for index, operation in enumerate(normalized_operations, start=1):
                current_output = (
                    output_path
                    if index == len(normalized_operations)
                    else temp_dir_path / f"step_{index}.pdf"
                )

                _apply_operation(
                    input_path=str(current_input),
                    output_path=str(current_output),
                    operation=operation,
                    attachment_paths=attachment_paths or [],
                )
                current_input = current_output

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'appliquer la sequence d'operations PDF.") from exc


def _validate_operations(operations: list[dict]) -> list[dict]:
    if not isinstance(operations, list) or not operations:
        raise InvalidFileError("Veuillez fournir au moins une operation pour le multi-outil PDF.")

    for operation in operations:
        if not isinstance(operation, dict):
            raise InvalidFileError("Chaque operation du multi-outil PDF doit etre un objet.")

    return operations


def _apply_operation(*, input_path: str, output_path: str, operation: dict, attachment_paths: list[str]):
    operation_name = _normalize_operation_name(operation)

    if operation_name == "delete-pages":
        delete_pdf_pages_file(
            input_path=input_path,
            output_path=output_path,
            pages_expression=_require_string_option(operation, "pages"),
        )
        return

    if operation_name == "extract-pages":
        extract_pdf_pages_file(
            input_path=input_path,
            output_path=output_path,
            pages_expression=_require_string_option(operation, "pages"),
        )
        return

    if operation_name == "organize-pdf":
        organize_pdf_file(
            input_path=input_path,
            output_path=output_path,
            page_order_expression=_require_string_option(
                operation,
                "order",
                fallback_keys=("pages",),
            ),
        )
        return

    if operation_name == "rotate-pdf":
        rotate_pdf_file(
            input_path=input_path,
            output_path=output_path,
            angle=int(operation.get("angle", 90)),
            pages_expression=str(operation.get("pages", "all")).strip() or "all",
        )
        return

    if operation_name == "rotate-custom":
        rotate_custom_pdf_file(
            input_path=input_path,
            output_path=output_path,
            rotations_expression=_require_string_option(
                operation,
                "rotations",
                fallback_keys=("pages",),
            ),
        )
        return

    if operation_name == "add-blank-page":
        page_number = operation.get("page")
        if page_number in (None, "", "null"):
            page_number = None
        else:
            page_number = int(page_number)

        add_blank_page_to_pdf_file(
            input_path=input_path,
            output_path=output_path,
            position=str(operation.get("position", "after")).strip().lower(),
            page_number=page_number,
            width=float(operation["width"]) if operation.get("width") not in (None, "", "null") else None,
            height=float(operation["height"]) if operation.get("height") not in (None, "", "null") else None,
        )
        return

    if operation_name == "reverse-pages":
        reverse_pdf_pages_file(input_path=input_path, output_path=output_path)
        return

    if operation_name == "n-up-pdf":
        n_up_pdf_file(
            input_path=input_path,
            output_path=output_path,
            pages_per_sheet=int(operation.get("pages_per_sheet", 4)),
        )
        return

    if operation_name == "grid-combine":
        grid_combine_pdf_file(
            input_path=input_path,
            output_path=output_path,
            rows=int(operation.get("rows", 2)),
            columns=int(operation.get("columns", 2)),
        )
        return

    if operation_name == "divide-pages":
        divide_pdf_pages_file(
            input_path=input_path,
            output_path=output_path,
            mode=str(operation.get("mode", "vertical")).strip().lower(),
        )
        return

    if operation_name == "combine-single-page":
        combine_pdf_into_single_page_file(
            input_path=input_path,
            output_path=output_path,
            gap=float(operation.get("gap", 0)),
        )
        return

    if operation_name == "posterize-pdf":
        posterize_pdf_file(
            input_path=input_path,
            output_path=output_path,
            rows=int(operation.get("rows", 2)),
            columns=int(operation.get("columns", 2)),
        )
        return

    if operation_name == "add-attachments":
        add_attachments_to_pdf_file(
            input_path=input_path,
            output_path=output_path,
            attachment_paths=attachment_paths,
        )
        return

    raise InvalidFileError(f"Operation multi-outil PDF non supportee : {operation_name}.")


def _normalize_operation_name(operation: dict) -> str:
    raw_name = operation.get("tool", operation.get("operation"))

    if not isinstance(raw_name, str) or not raw_name.strip():
        raise InvalidFileError("Chaque operation doit preciser un outil.")

    normalized_name = raw_name.strip().lower()
    return ALIASES.get(normalized_name, normalized_name)


def _require_string_option(
    operation: dict,
    key: str,
    *,
    fallback_keys: tuple[str, ...] = (),
) -> str:
    for candidate_key in (key, *fallback_keys):
        value = operation.get(candidate_key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    raise InvalidFileError(f"L'option {key} est requise pour cette operation PDF.")
