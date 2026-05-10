from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def decrypt_pdf_file(
    *,
    input_path: str,
    output_path: str,
    password: str,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not password:
        raise InvalidFileError("Le mot de passe du PDF est requis.")

    try:
        reader = PdfReader(str(input_path))

        if not reader.is_encrypted:
            raise InvalidFileError("Le PDF n'est pas chiffre.")

        if reader.decrypt(password) == 0:
            raise ProtectedFileError("Mot de passe PDF invalide.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        if reader.metadata:
            writer.add_metadata(dict(reader.metadata))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de dechiffrer ce PDF.") from exc
