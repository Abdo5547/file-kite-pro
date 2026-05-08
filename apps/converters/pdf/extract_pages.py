from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError
from apps.converters.pdf.split import parse_pages_expression


def extract_pdf_pages_file(
    *,
    input_path: str,
    output_path: str,
    pages_expression: str,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protégé par mot de passe.")

        total_pages = len(reader.pages)

        if total_pages == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        pages_to_extract = parse_pages_expression(
            pages_expression,
            preserve_order=True,
        )

        writer = PdfWriter()

        for page_number in pages_to_extract:
            if page_number < 1 or page_number > total_pages:
                raise InvalidFileError(
                    f"La page {page_number} est invalide. Le PDF contient {total_pages} page(s)."
                )

            writer.add_page(reader.pages[page_number - 1])

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'extraire les pages de ce PDF.") from exc
