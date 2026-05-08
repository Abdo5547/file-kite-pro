from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def ocr_pdf_file(*, input_path: str, output_path: str, language: str = "fra+eng") -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)
    language = str(language or "fra+eng").strip() or "fra+eng"

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protege par mot de passe.")

        if len(reader.pages) == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        writer.add_metadata(
            {
                "/Producer": "File Kite Pro OCR preparation",
                "/OCRLanguage": language,
                "/OCRStatus": "prepared",
                "/OCRNote": (
                    "OCR engine integration is required to add a searchable text layer."
                ),
            }
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de preparer l'OCR pour ce PDF.") from exc
