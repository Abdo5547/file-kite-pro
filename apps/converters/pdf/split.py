from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def split_pdf_file(
    *,
    input_path: str,
    output_dir: str,
    pages: list[int] | None = None,
) -> list[str]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protégé par mot de passe.")

        total_pages = len(reader.pages)

        if total_pages == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        if pages is None:
            pages = list(range(1, total_pages + 1))

        output_paths = []

        for page_number in pages:
            if page_number < 1 or page_number > total_pages:
                raise InvalidFileError(
                    f"La page {page_number} est invalide. Le PDF contient {total_pages} page(s)."
                )

            writer = PdfWriter()
            writer.add_page(reader.pages[page_number - 1])

            output_path = output_dir / f"page_{page_number}.pdf"

            with output_path.open("wb") as output_file:
                writer.write(output_file)

            output_paths.append(str(output_path))

        return output_paths

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de diviser ce fichier PDF.") from exc


def parse_pages_expression(expression: str) -> list[int]:
    """
    Convertit une expression comme:
    "1,3,5-7" → [1, 3, 5, 6, 7]
    """
    if not expression:
        raise InvalidFileError("Veuillez fournir les pages à extraire.")

    pages = set()

    parts = expression.replace(" ", "").split(",")

    for part in parts:
        if not part:
            continue

        if "-" in part:
            start_raw, end_raw = part.split("-", 1)

            if not start_raw.isdigit() or not end_raw.isdigit():
                raise InvalidFileError("Format de pages invalide.")

            start = int(start_raw)
            end = int(end_raw)

            if start > end:
                raise InvalidFileError("La plage de pages est invalide.")

            for page in range(start, end + 1):
                pages.add(page)

        else:
            if not part.isdigit():
                raise InvalidFileError("Format de pages invalide.")

            pages.add(int(part))

    if not pages:
        raise InvalidFileError("Aucune page valide fournie.")

    return sorted(pages)