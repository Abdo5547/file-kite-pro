from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def remove_pdf_metadata(
    *,
    input_path: str,
    output_path: str,
    password: str | None = None,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            if not password or reader.decrypt(password) == 0:
                raise ProtectedFileError("Le PDF est protege et necessite un mot de passe valide.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        writer.add_metadata({})

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de supprimer les metadonnees de ce PDF.") from exc
