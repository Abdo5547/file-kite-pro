from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


SUPPORTED_DIVIDE_MODES = {"vertical", "horizontal", "quarters"}


def divide_pdf_pages_file(*, input_path: str, output_path: str, mode: str = "vertical") -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)
    normalized_mode = str(mode or "vertical").strip().lower()

    if normalized_mode not in SUPPORTED_DIVIDE_MODES:
        raise InvalidFileError("Modes supportes: vertical, horizontal, quarters.")

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
            for x, y, part_width, part_height in _get_divisions(width, height, normalized_mode):
                part_page = PageObject.create_blank_page(width=part_width, height=part_height)
                transformation = Transformation().translate(-x, -y)
                part_page.merge_transformed_page(page, transformation)
                writer.add_page(part_page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de diviser les pages de ce PDF.") from exc


def _get_divisions(width: float, height: float, mode: str):
    half_width = width / 2
    half_height = height / 2

    if mode == "vertical":
        return [
            (0, 0, half_width, height),
            (half_width, 0, half_width, height),
        ]

    if mode == "horizontal":
        return [
            (0, half_height, width, half_height),
            (0, 0, width, half_height),
        ]

    return [
        (0, half_height, half_width, half_height),
        (half_width, half_height, half_width, half_height),
        (0, 0, half_width, half_height),
        (half_width, 0, half_width, half_height),
    ]
