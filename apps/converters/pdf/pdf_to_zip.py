import json
import zipfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


def export_pdf_to_zip_file(*, input_path: str, output_zip_path: str) -> str:
    input_path = Path(input_path)
    output_zip_path = Path(output_zip_path)

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            raise ProtectedFileError("Le fichier PDF est protege par mot de passe.")

        if len(reader.pages) == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        output_zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            manifest = {
                "source": input_path.name,
                "page_count": len(reader.pages),
                "files": [],
            }

            for page_index, page in enumerate(reader.pages, start=1):
                page_writer = PdfWriter()
                page_writer.add_page(page)

                page_filename = f"pages/page_{page_index:04d}.pdf"
                with zip_file.open(page_filename, "w") as page_file:
                    page_writer.write(page_file)

                manifest["files"].append(page_filename)

            metadata = {
                str(key): str(value)
                for key, value in (reader.metadata or {}).items()
                if value is not None
            }
            if metadata:
                metadata_filename = "metadata.json"
                zip_file.writestr(
                    metadata_filename,
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                )
                manifest["files"].append(metadata_filename)

            zip_file.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )

        return str(output_zip_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible d'exporter ce PDF en ZIP.") from exc
