from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def combine_pdf_into_single_page_file(*, input_path: str, output_path: str, gap: float = 0.0) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if gap < 0:
        raise InvalidFileError("L'espacement doit etre positif.")

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))
        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protege par mot de passe.")

        pages = list(reader.pages)
        if not pages:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        max_width = max(float(page.mediabox.width) for page in pages)
        total_height = sum(float(page.mediabox.height) for page in pages) + gap * (len(pages) - 1)

        combined_page = PageObject.create_blank_page(width=max_width, height=total_height)
        current_y = total_height

        for page in pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            current_y -= height
            offset_x = (max_width - width) / 2
            transformation = Transformation().translate(offset_x, current_y)
            combined_page.merge_transformed_page(page, transformation)
            current_y -= gap

        writer = PdfWriter()
        writer.add_page(combined_page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de combiner les pages sur une seule page.") from exc
