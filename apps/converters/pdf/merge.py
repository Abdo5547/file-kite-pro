from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def merge_pdf_files(input_paths: Iterable[str], output_path: str) -> str:
    writer = PdfWriter()
    input_paths = list(input_paths)

    if len(input_paths) < 2:
        raise InvalidFileError("Au moins deux fichiers PDF sont nécessaires.")

    for input_path in input_paths:
        path = Path(input_path)

        if not path.exists():
            raise InvalidFileError(f"Fichier introuvable : {path.name}")

        try:
            reader = PdfReader(str(path))

            if reader.is_encrypted:
                raise ProtectedFileError(
                    f"Le fichier {path.name} est protégé par mot de passe."
                )

            if len(reader.pages) == 0:
                raise InvalidFileError(
                    f"Le fichier {path.name} ne contient aucune page."
                )

            for page in reader.pages:
                writer.add_page(page)

        except (InvalidFileError, ProtectedFileError):
            raise
        except Exception as exc:
            raise InvalidFileError(
                f"Impossible de lire le fichier PDF : {path.name}"
            ) from exc

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("wb") as file:
        writer.write(file)

    return str(output)