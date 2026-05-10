from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.constants import UserAccessPermissions

from apps.converters.exceptions import InvalidFileError, ProtectedFileError


PERMISSION_MAP = {
    "print": UserAccessPermissions.PRINT,
    "modify": UserAccessPermissions.MODIFY,
    "extract": UserAccessPermissions.EXTRACT,
    "add_or_modify": UserAccessPermissions.ADD_OR_MODIFY,
    "fill_forms": UserAccessPermissions.FILL_FORM_FIELDS,
    "assemble": UserAccessPermissions.ASSEMBLE_DOC,
    "print_high_quality": UserAccessPermissions.PRINT_TO_REPRESENTATION,
}


def change_pdf_permissions(
    *,
    input_path: str,
    output_path: str,
    user_password: str,
    owner_password: str,
    allowed_permissions: list[str],
    source_password: str | None = None,
    algorithm: str = "AES-256",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not user_password:
        raise InvalidFileError("Le mot de passe utilisateur est requis.")

    if not owner_password:
        raise InvalidFileError("Le mot de passe proprietaire est requis.")

    permissions_flag = _build_permissions_flag(allowed_permissions)

    try:
        reader = PdfReader(str(input_path))

        if reader.is_encrypted:
            password = source_password or owner_password
            if reader.decrypt(password) == 0:
                raise ProtectedFileError("Impossible d'ouvrir le PDF avec le mot de passe fourni.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        if reader.metadata:
            writer.add_metadata(dict(reader.metadata))

        writer.encrypt(
            user_password=user_password,
            owner_password=owner_password,
            permissions_flag=permissions_flag,
            algorithm=algorithm,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    except (InvalidFileError, ProtectedFileError):
        raise
    except Exception as exc:
        raise InvalidFileError("Impossible de modifier les permissions de ce PDF.") from exc


def _build_permissions_flag(allowed_permissions: list[str]) -> UserAccessPermissions:
    permissions = UserAccessPermissions(0)

    for permission in allowed_permissions:
        normalized = str(permission).strip().lower()
        if normalized not in PERMISSION_MAP:
            raise InvalidFileError(f"Permission PDF non supportee : {permission}")
        permissions |= PERMISSION_MAP[normalized]

    return permissions
