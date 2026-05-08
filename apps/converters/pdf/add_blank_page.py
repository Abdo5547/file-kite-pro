from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def add_blank_page_to_pdf_file(
    *,
    input_path: str,
    output_path: str,
    position: str,
    page_number: int | None = None,
    width: float | None = None,
    height: float | None = None,
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

        insert_index = resolve_blank_page_insert_index(
            position=position,
            page_number=page_number,
            total_pages=total_pages,
        )

        reference_page = reader.pages[min(insert_index, total_pages - 1)] if insert_index < total_pages else reader.pages[-1]
        blank_width = float(width) if width is not None else float(reference_page.mediabox.width)
        blank_height = float(height) if height is not None else float(reference_page.mediabox.height)

        blank_page = PageObject.create_blank_page(width=blank_width, height=blank_height)

        writer = PdfWriter()
        inserted = False

        for index, page in enumerate(reader.pages):
            if index == insert_index:
                writer.add_page(blank_page)
                inserted = True
            writer.add_page(page)

        if not inserted:
            writer.add_page(blank_page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'ajouter une page blanche au PDF.") from exc


def resolve_blank_page_insert_index(*, position: str, page_number: int | None, total_pages: int) -> int:
    normalized_position = str(position or "after").strip().lower()

    if normalized_position == "start":
        return 0
    if normalized_position == "end":
        return total_pages

    if page_number is None:
        raise InvalidFileError("Veuillez préciser la page cible pour l'insertion.")

    if page_number < 1 or page_number > total_pages:
        raise InvalidFileError(
            f"La page {page_number} est invalide. Le PDF contient {total_pages} page(s)."
        )

    if normalized_position == "before":
        return page_number - 1
    if normalized_position == "after":
        return page_number

    raise InvalidFileError("Position non supportée. Utilisez start, end, before ou after.")
