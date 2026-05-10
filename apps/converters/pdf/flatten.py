from pathlib import Path

import fitz

from apps.converters.exceptions import InvalidFileError


def flatten_pdf_file(
    *,
    input_path: str,
    output_path: str,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    document = None

    try:
        document = fitz.open(str(input_path))

        for page in document:
            widgets = list(page.widgets() or [])
            for widget in widgets:
                page.delete_widget(widget)

            annotations = list(page.annots() or [])
            for annot in annotations:
                page.delete_annot(annot)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output_path), garbage=4, deflate=True, clean=True)
        return str(output_path)

    except Exception as exc:
        raise InvalidFileError("Impossible d'aplatir ce PDF.") from exc
    finally:
        if document is not None:
            document.close()
