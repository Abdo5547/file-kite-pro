from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


SUPPORTED_ANGLES = {90, 180, 270}


def rotate_custom_pdf_file(*, input_path: str, output_path: str, rotations_expression: str) -> str:
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

        rotations = parse_rotations_expression(rotations_expression, total_pages=total_pages)

        writer = PdfWriter()
        for index, page in enumerate(reader.pages, start=1):
            angle = rotations.get(index)
            if angle is not None:
                page.rotate(angle)
            writer.add_page(page)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'appliquer la rotation personnalisée au PDF.") from exc


def parse_rotations_expression(rotations_expression: str, *, total_pages: int) -> dict[int, int]:
    expression = str(rotations_expression or "").replace(" ", "")
    if not expression:
        raise InvalidFileError("Veuillez fournir les rotations personnalisées.")

    rotations: dict[int, int] = {}
    parts = expression.split(",")

    for part in parts:
        if not part or ":" not in part:
            raise InvalidFileError("Format de rotation personnalisée invalide.")

        page_raw, angle_raw = part.split(":", 1)
        if not page_raw.isdigit() or not angle_raw.lstrip("-").isdigit():
            raise InvalidFileError("Format de rotation personnalisée invalide.")

        page_number = int(page_raw)
        angle = int(angle_raw)

        if page_number < 1 or page_number > total_pages:
            raise InvalidFileError(
                f"La page {page_number} est invalide. Le PDF contient {total_pages} page(s)."
            )

        if angle not in SUPPORTED_ANGLES:
            raise InvalidFileError("Angles autorisés : 90, 180, 270.")

        if page_number in rotations:
            raise InvalidFileError("Chaque page ne peut recevoir qu'une seule rotation.")

        rotations[page_number] = angle

    return rotations
