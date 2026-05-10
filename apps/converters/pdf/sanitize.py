from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def sanitize_pdf_file(
    *,
    input_path: str,
    output_path: str,
    password: str | None = None,
    remove_links: bool = True,
    remove_file_attachments: bool = True,
    remove_javascript: bool = True,
    remove_metadata: bool = True,
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            if not password or reader.decrypt(password) == 0:
                raise ProtectedFileError("Le PDF est protege et necessite un mot de passe valide.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        if reader.metadata and not remove_metadata:
            writer.add_metadata(dict(reader.metadata))
        else:
            writer.add_metadata({})

        if remove_links:
            writer.remove_links()

        if remove_file_attachments:
            writer.remove_annotations(["/FileAttachment"])

        if remove_javascript:
            _strip_javascript(writer)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de nettoyer ce PDF.") from exc


def _strip_javascript(writer: PdfWriter) -> None:
    root = writer._root_object

    for key in ("/OpenAction", "/AA"):
        if key in root:
            del root[key]

    names = root.get("/Names")
    if not isinstance(names, DictionaryObject):
        return

    if NameObject("/JavaScript") in names:
        del names[NameObject("/JavaScript")]
