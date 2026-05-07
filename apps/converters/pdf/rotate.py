from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError
from apps.converters.pdf.split import parse_pages_expression


SUPPORTED_ANGLES = {90, 180, 270}


def rotate_pdf_file(
    *,
    input_path: str,
    output_path: str,
    angle: int,
    pages_expression: str = "all",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if angle not in SUPPORTED_ANGLES:
        raise InvalidFileError("Angle non supporté. Utilisez 90, 180 ou 270.")

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protégé par mot de passe.")

        total_pages = len(reader.pages)

        if total_pages == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        pages_to_rotate = get_pages_to_rotate(
            pages_expression=pages_expression,
            total_pages=total_pages,
        )

        writer = PdfWriter()

        for index, page in enumerate(reader.pages, start=1):
            if index in pages_to_rotate:
                page.rotate(angle)

            writer.add_page(page)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de faire pivoter ce PDF.") from exc


def get_pages_to_rotate(*, pages_expression: str, total_pages: int) -> set[int]:
    pages_expression = str(pages_expression or "all").strip().lower()

    if pages_expression == "all":
        return set(range(1, total_pages + 1))

    pages = parse_pages_expression(pages_expression)

    for page_number in pages:
        if page_number < 1 or page_number > total_pages:
            raise InvalidFileError(
                f"La page {page_number} est invalide. Le PDF contient {total_pages} page(s)."
            )

    return set(pages)