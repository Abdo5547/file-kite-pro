from pathlib import Path

import pypdfium2 as pdfium

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


SUPPORTED_IMAGE_FORMATS = {"png", "jpg", "jpeg"}


def pdf_to_images_files(
    *,
    input_path: str,
    output_dir: str,
    output_format: str = "png",
    scale: float = 2.0,
) -> list[str]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    output_format = output_format.lower().strip()

    if output_format == "jpeg":
        output_format = "jpg"

    if output_format not in SUPPORTED_IMAGE_FORMATS:
        raise InvalidFileError("Format de sortie non supporté. Utilisez png ou jpg.")

    if not input_path.exists():
        raise InvalidFileError("Fichier PDF introuvable.")

    if scale <= 0 or scale > 5:
        raise InvalidFileError("Le scale doit être compris entre 0.1 et 5.")

    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = None

    try:
        # Important Windows:
        # On lit le PDF en mémoire pour éviter que pypdfium2 verrouille le fichier temporaire.
        pdf_bytes = input_path.read_bytes()
        pdf = pdfium.PdfDocument(pdf_bytes)

        page_count = len(pdf)

        if page_count == 0:
            raise InvalidFileError("Le PDF ne contient aucune page.")

        output_paths = []

        for index in range(page_count):
            page = None
            bitmap = None

            try:
                page = pdf[index]
                bitmap = page.render(scale=scale)
                pil_image = bitmap.to_pil()

                output_path = output_dir / f"page_{index + 1}.{output_format}"

                if output_format == "jpg":
                    pil_image = pil_image.convert("RGB")
                    pil_image.save(
                        output_path,
                        format="JPEG",
                        quality=90,
                        optimize=True,
                    )
                else:
                    if pil_image.mode not in ("RGB", "RGBA"):
                        pil_image = pil_image.convert("RGBA")

                    pil_image.save(
                        output_path,
                        format="PNG",
                        optimize=True,
                    )

                output_paths.append(str(output_path))

            finally:
                if bitmap is not None:
                    bitmap.close()

                if page is not None:
                    page.close()

        return output_paths

    except InvalidFileError:
        raise

    except Exception as exc:
        message = str(exc).lower()

        if "password" in message or "encrypted" in message:
            raise ProtectedFileError("Le fichier PDF est protégé par mot de passe.") from exc

        raise InvalidFileError(f"Impossible de convertir ce PDF en images : {exc}") from exc

    finally:
        if pdf is not None:
            pdf.close()