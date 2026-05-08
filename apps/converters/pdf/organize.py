from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError
from apps.converters.pdf.split import parse_pages_expression


def organize_pdf_file(
    *,
    input_path: str,
    output_path: str,
    page_order_expression: str,
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

        page_order = parse_pages_expression(
            page_order_expression,
            preserve_order=True,
        )

        if sorted(page_order) != list(range(1, total_pages + 1)):
            raise InvalidFileError(
                "L'ordre des pages doit contenir chaque page du PDF une seule fois."
            )

        writer = PdfWriter()

        for page_number in page_order:
            writer.add_page(reader.pages[page_number - 1])

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de réorganiser ce PDF.") from exc
