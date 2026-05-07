from pathlib import Path

from PIL import Image, UnidentifiedImageError

from apps.converters.exceptions import InvalidFileError, UnsupportedConversionError
from apps.converters.images.convert import normalize_format, prepare_for_jpeg


SUPPORTED_OPERATIONS = {
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "flip_horizontal",
    "flip_vertical",
}


def rotate_flip_image_file(
    *,
    input_path: str,
    output_path: str,
    operation: str,
    output_format: str = "webp",
    quality: int = 85,
    background: str = "#ffffff",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    operation = operation.lower().strip()
    output_format = normalize_format(output_format)

    if operation not in SUPPORTED_OPERATIONS:
        raise UnsupportedConversionError(
            f"Opération image non supportée : {operation}"
        )

    try:
        with Image.open(input_path) as image:
            image.load()

            result = apply_operation(image, operation)

            if output_format == "jpeg":
                result = prepare_for_jpeg(result, background)
            elif output_format in {"png", "webp"}:
                result = result.convert("RGBA")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            save_kwargs = {}

            if output_format in {"jpeg", "webp"}:
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True

            if output_format == "png":
                save_kwargs["optimize"] = True
                save_kwargs["compress_level"] = 9

            result.save(
                output_path,
                format="JPEG" if output_format == "jpeg" else output_format.upper(),
                **save_kwargs,
            )

    except UnidentifiedImageError as exc:
        raise InvalidFileError("Image invalide ou corrompue.") from exc
    except OSError as exc:
        raise InvalidFileError("Impossible de transformer cette image.") from exc

    return str(output_path)


def apply_operation(image: Image.Image, operation: str) -> Image.Image:
    if operation == "rotate_90":
        return image.rotate(-90, expand=True)

    if operation == "rotate_180":
        return image.rotate(180, expand=True)

    if operation == "rotate_270":
        return image.rotate(-270, expand=True)

    if operation == "flip_horizontal":
        return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    if operation == "flip_vertical":
        return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    raise UnsupportedConversionError(
        f"Opération image non supportée : {operation}"
    )