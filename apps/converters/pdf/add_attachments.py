from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def add_attachments_to_pdf_file(
    *,
    input_path: str,
    output_path: str,
    attachment_paths: list[str],
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not attachment_paths:
        raise InvalidFileError("Aucun fichier joint a ajouter au PDF.")

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protege par mot de passe.")

        if len(reader.pages) == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        writer = PdfWriter()
        writer.clone_document_from_reader(reader)

        used_names = {
            attachment.name
            for attachment in reader.attachment_list
            if getattr(attachment, "name", None)
        }

        for index, attachment_path_raw in enumerate(attachment_paths, start=1):
            attachment_path = Path(attachment_path_raw)

            if not attachment_path.exists():
                raise InvalidFileError(
                    f"Le fichier joint {attachment_path.name} est introuvable."
                )

            attachment_name = _build_unique_attachment_name(
                attachment_path.name or f"attachment_{index}",
                used_names,
            )

            with attachment_path.open("rb") as attachment_file:
                writer.add_attachment(attachment_name, attachment_file.read())

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'ajouter les pieces jointes a ce PDF.") from exc


def _build_unique_attachment_name(filename: str, used_names: set[str]) -> str:
    safe_name = Path(filename).name.strip() or "attachment"
    stem = Path(safe_name).stem or "attachment"
    suffix = Path(safe_name).suffix
    candidate = safe_name
    counter = 2

    while candidate in used_names:
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1

    used_names.add(candidate)
    return candidate
