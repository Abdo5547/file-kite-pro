from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def alternate_merge_pdf_files(*, input_paths, output_path: str) -> str:
    input_paths = [Path(path) for path in input_paths]
    output_path = Path(output_path)

    if len(input_paths) != 2:
        raise InvalidFileError("La fusion alternée requiert exactement deux fichiers PDF.")

    for path in input_paths:
        if not path.exists():
            raise InvalidFileError(f"Fichier introuvable : {path.name}")

    try:
        readers = [PdfReader(str(path)) for path in input_paths]

        for path, reader in zip(input_paths, readers):
            if reader.is_encrypted:
                raise ProtectedFileError(
                    f"Le fichier {path.name} est protégé par mot de passe."
                )
            if len(reader.pages) == 0:
                raise InvalidFileError(
                    f"Le fichier {path.name} ne contient aucune page."
                )

        writer = PdfWriter()
        max_pages = max(len(reader.pages) for reader in readers)

        for page_index in range(max_pages):
            for reader in readers:
                if page_index < len(reader.pages):
                    writer.add_page(reader.pages[page_index])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de fusionner les PDFs en alternance.") from exc
