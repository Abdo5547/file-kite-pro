from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def encrypt_pdf_file(
    *,
    input_path: str,
    output_path: str,
    user_password: str,
    owner_password: str | None = None,
    algorithm: str = "AES-256",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not user_password:
        raise InvalidFileError("Le mot de passe utilisateur est requis.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le PDF est deja protege par mot de passe.")

        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        if reader.metadata:
            writer.add_metadata(dict(reader.metadata))

        writer.encrypt(
            user_password=user_password,
            owner_password=owner_password or user_password,
            algorithm=algorithm,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de chiffrer ce PDF.") from exc
