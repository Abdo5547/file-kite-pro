from pathlib import Path

import fitz

from apps.converters.exceptions import InvalidFileError


def find_and_redact_text_in_pdf(
    *,
    input_path: str,
    output_path: str,
    search_text: str,
    replacement_text: str = "",
    fill_color: tuple[float, float, float] = (0, 0, 0),
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not search_text.strip():
        raise InvalidFileError("Le texte a masquer est requis.")

    document = None

    try:
        document = fitz.open(str(input_path))

        matches = 0
        for page in document:
            areas = page.search_for(search_text)
            for area in areas:
                page.add_redact_annot(area, text=replacement_text, fill=fill_color)
                matches += 1

            if areas:
                page.apply_redactions()

        if matches == 0:
            raise InvalidFileError("Aucune occurrence du texte a masquer n'a ete trouvee.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output_path), garbage=4, deflate=True, clean=True)
        return str(output_path)

    except InvalidFileError:
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de chercher et masquer ce texte dans le PDF.") from exc
    finally:
        if document is not None:
            document.close()
