from pathlib import Path

from pypdf import PdfReader

from apps.converters.exceptions import InvalidFileError, ProcessingLimitError, ProtectedFileError
from PIL import Image, UnidentifiedImageError


ALLOWED_PDF_EXTENSIONS = {".pdf"}


def validate_uploaded_files(uploaded_files, limits):
    if not uploaded_files:
        raise InvalidFileError("Aucun fichier reçu.")

    if len(uploaded_files) > limits.max_files:
        raise ProcessingLimitError(
            f"Maximum {limits.max_files} fichier(s) autorisé(s) pour votre plan."
        )

    total_size = 0

    for uploaded_file in uploaded_files:
        if uploaded_file.size == 0:
            raise InvalidFileError(f"Le fichier {uploaded_file.name} est vide.")

        if uploaded_file.size > limits.max_file_size:
            max_mb = limits.max_file_size // (1024 * 1024)
            raise ProcessingLimitError(
                f"Le fichier {uploaded_file.name} dépasse la limite de {max_mb} Mo."
            )

        total_size += uploaded_file.size

    if total_size > limits.max_total_size:
        max_total_mb = limits.max_total_size // (1024 * 1024)
        raise ProcessingLimitError(
            f"La taille totale dépasse la limite de {max_total_mb} Mo."
        )

    return total_size


def validate_pdf_uploaded_files(uploaded_files, limits, min_files=1):
    if len(uploaded_files) < min_files:
        raise InvalidFileError(
            f"Veuillez envoyer au moins {min_files} fichier(s) PDF."
        )

    total_size = validate_uploaded_files(uploaded_files, limits)

    for uploaded_file in uploaded_files:
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_PDF_EXTENSIONS:
            raise InvalidFileError(
                f"Le fichier {uploaded_file.name} n'a pas une extension PDF valide."
            )

        _validate_pdf_signature(uploaded_file)

    return total_size


def validate_pdf_file_on_disk(file_path):
    file_path = Path(file_path)

    try:
        with file_path.open("rb") as pdf_file:
            reader = PdfReader(pdf_file)

            if reader.is_encrypted:
                raise ProtectedFileError(
                    f"Le fichier {file_path.name} est protégé par mot de passe."
                )

            if len(reader.pages) == 0:
                raise InvalidFileError(
                    f"Le fichier {file_path.name} ne contient aucune page."
                )

    except ProtectedFileError:
        raise
    except InvalidFileError:
        raise
    except Exception as exc:
        raise InvalidFileError(
            f"Le fichier {file_path.name} est invalide ou corrompu."
        ) from exc


def _validate_pdf_signature(uploaded_file):
    current_position = uploaded_file.tell()

    try:
        uploaded_file.seek(0)
        signature = uploaded_file.read(5)

        if signature != b"%PDF-":
            raise InvalidFileError(
                f"Le fichier {uploaded_file.name} ne semble pas être un vrai PDF."
            )
    finally:
        uploaded_file.seek(current_position)





ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image_uploaded_files(uploaded_files, limits, min_files=1):
    if len(uploaded_files) < min_files:
        raise InvalidFileError(
            f"Veuillez envoyer au moins {min_files} image(s)."
        )

    total_size = validate_uploaded_files(uploaded_files, limits)

    for uploaded_file in uploaded_files:
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise InvalidFileError(
                f"Le fichier {uploaded_file.name} n'a pas une extension image valide."
            )

        validate_image_signature(uploaded_file)

    return total_size


def validate_image_signature(uploaded_file):
    current_position = uploaded_file.tell()

    try:
        uploaded_file.seek(0)

        try:
            image = Image.open(uploaded_file)
            image.verify()
        except UnidentifiedImageError as exc:
            raise InvalidFileError(
                f"Le fichier {uploaded_file.name} n'est pas une image valide."
            ) from exc
        except Exception as exc:
            raise InvalidFileError(
                f"Le fichier {uploaded_file.name} est invalide ou corrompu."
            ) from exc

    finally:
        uploaded_file.seek(current_position)