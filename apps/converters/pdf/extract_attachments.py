from pathlib import Path

from pypdf import PdfReader

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def extract_pdf_attachments(*, input_path: str, output_dir: str) -> list[str]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protege par mot de passe.")

        attachments = list(reader.attachment_list)
        if not attachments:
            raise InvalidFileError("Aucune piece jointe trouvee dans ce PDF.")

        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_paths: list[str] = []
        used_names: set[str] = set()

        for index, attachment in enumerate(attachments, start=1):
            filename = attachment.name or attachment.alternative_name or f"attachment_{index}"
            safe_name = _build_unique_attachment_name(filename, used_names)
            content = _normalize_attachment_content(attachment.content)

            output_path = output_dir / safe_name
            with output_path.open("wb") as output_file:
                output_file.write(content)

            extracted_paths.append(str(output_path))

        return extracted_paths

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'extraire les pieces jointes de ce PDF.") from exc


def _normalize_attachment_content(content) -> bytes:
    if isinstance(content, bytes):
        return content

    if isinstance(content, bytearray):
        return bytes(content)

    if isinstance(content, str):
        return content.encode("utf-8")

    if isinstance(content, list):
        chunks: list[bytes] = []
        for item in content:
            if isinstance(item, bytes):
                chunks.append(item)
            elif isinstance(item, bytearray):
                chunks.append(bytes(item))
            elif isinstance(item, str):
                chunks.append(item.encode("utf-8"))
            else:
                raise InvalidFileError("Une piece jointe du PDF est invalide.")
        return b"".join(chunks)

    raise InvalidFileError("Une piece jointe du PDF est invalide.")


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
