import math
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


SUPPORTED_N_UP = {
    2: (1, 2),
    4: (2, 2),
    6: (2, 3),
    8: (2, 4),
}


def grid_combine_pdf_file(
    *,
    input_path: str,
    output_path: str,
    rows: int,
    columns: int,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if rows < 1 or columns < 1:
        raise InvalidFileError("La grille doit contenir au moins 1 ligne et 1 colonne.")

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protégé par mot de passe.")

        pages = list(reader.pages)
        if not pages:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        max_width = max(float(page.mediabox.width) for page in pages)
        max_height = max(float(page.mediabox.height) for page in pages)
        output_width = max_width * columns
        output_height = max_height * rows

        writer = PdfWriter()
        pages_per_sheet = rows * columns

        for start in range(0, len(pages), pages_per_sheet):
            sheet = PageObject.create_blank_page(width=output_width, height=output_height)
            batch = pages[start : start + pages_per_sheet]

            for index, page in enumerate(batch):
                row = index // columns
                column = index % columns
                _merge_page_into_grid_cell(
                    target_page=sheet,
                    source_page=page,
                    row=row,
                    column=column,
                    rows=rows,
                    columns=columns,
                    cell_width=max_width,
                    cell_height=max_height,
                )

            writer.add_page(sheet)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de combiner les pages en grille.") from exc


def n_up_pdf_file(*, input_path: str, output_path: str, pages_per_sheet: int) -> str:
    if pages_per_sheet not in SUPPORTED_N_UP:
        raise InvalidFileError("Valeurs supportées pour n-up : 2, 4, 6 ou 8.")

    rows, columns = SUPPORTED_N_UP[pages_per_sheet]
    return grid_combine_pdf_file(
        input_path=input_path,
        output_path=output_path,
        rows=rows,
        columns=columns,
    )


def _merge_page_into_grid_cell(
    *,
    target_page,
    source_page,
    row: int,
    column: int,
    rows: int,
    columns: int,
    cell_width: float,
    cell_height: float,
):
    source_width = float(source_page.mediabox.width)
    source_height = float(source_page.mediabox.height)

    scale = min(cell_width / source_width, cell_height / source_height)
    scaled_width = source_width * scale
    scaled_height = source_height * scale

    offset_x = column * cell_width + (cell_width - scaled_width) / 2
    offset_y = (rows - 1 - row) * cell_height + (cell_height - scaled_height) / 2

    transformation = Transformation().scale(scale, scale).translate(offset_x, offset_y)
    target_page.merge_transformed_page(source_page, transformation)
