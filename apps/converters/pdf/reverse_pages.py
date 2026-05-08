from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def reverse_pdf_pages_file(*, input_path: str, output_path: str) -> str:
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

        writer = PdfWriter()
        for page in reversed(reader.pages):
            writer.add_page(page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'inverser les pages de ce PDF.") from exc
