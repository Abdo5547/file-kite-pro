from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def posterize_pdf_file(*, input_path: str, output_path: str, rows: int = 2, columns: int = 2) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if rows < 1 or columns < 1:
        raise InvalidFileError("Les dimensions du poster doivent etre superieures a zero.")

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))
        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protege par mot de passe.")
        if len(reader.pages) == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        writer = PdfWriter()
        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            tile_width = width / columns
            tile_height = height / rows

            for row in range(rows):
                for column in range(columns):
                    tile_page = PageObject.create_blank_page(width=tile_width, height=tile_height)
                    offset_x = -column * tile_width
                    offset_y = -(rows - 1 - row) * tile_height
                    transformation = Transformation().translate(offset_x, offset_y)
                    tile_page.merge_transformed_page(page, transformation)
                    writer.add_page(tile_page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de transformer ce PDF en poster imprimable.") from exc
