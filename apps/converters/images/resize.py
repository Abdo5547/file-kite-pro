from pathlib import Path

from PIL import Image, UnidentifiedImageError

from apps.converters.exceptions import InvalidFileError, ProcessingLimitError
from apps.converters.images.convert import prepare_for_jpeg, normalize_format


MAX_IMAGE_DIMENSION = 10000


def resize_image_file(
    *,
    input_path: str,
    output_path: str,
    width: int | None = None,
    height: int | None = None,
    keep_ratio: bool = True,
    output_format: str = "webp",
    quality: int = 85,
    background: str = "#ffffff",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    output_format = normalize_format(output_format)

    if not width and not height:
        raise InvalidFileError("Veuillez fournir une largeur ou une hauteur.")

    if width is not None and width <= 0:
        raise InvalidFileError("La largeur doit être supérieure à 0.")

    if height is not None and height <= 0:
        raise InvalidFileError("La hauteur doit être supérieure à 0.")

    if width and width > MAX_IMAGE_DIMENSION:
        raise ProcessingLimitError(
            f"La largeur maximale autorisée est {MAX_IMAGE_DIMENSION}px."
        )

    if height and height > MAX_IMAGE_DIMENSION:
        raise ProcessingLimitError(
            f"La hauteur maximale autorisée est {MAX_IMAGE_DIMENSION}px."
        )

    try:
        with Image.open(input_path) as image:
            image.load()

            original_width, original_height = image.size

            new_width, new_height = calculate_new_size(
                original_width=original_width,
                original_height=original_height,
                width=width,
                height=height,
                keep_ratio=keep_ratio,
            )

            resized = image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS,
            )

            if output_format == "jpeg":
                resized = prepare_for_jpeg(resized, background)
            elif output_format in {"png", "webp"}:
                resized = resized.convert("RGBA")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            save_kwargs = {}

            if output_format in {"jpeg", "webp"}:
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True

            resized.save(
                output_path,
                format="JPEG" if output_format == "jpeg" else output_format.upper(),
                **save_kwargs,
            )

    except UnidentifiedImageError as exc:
        raise InvalidFileError("Image invalide ou corrompue.") from exc
    except OSError as exc:
        raise InvalidFileError("Impossible de redimensionner cette image.") from exc

    return str(output_path)


def calculate_new_size(
    *,
    original_width: int,
    original_height: int,
    width: int | None,
    height: int | None,
    keep_ratio: bool,
) -> tuple[int, int]:
    if not keep_ratio:
        return width or original_width, height or original_height

    if width and not height:
        ratio = width / original_width
        return width, max(1, round(original_height * ratio))

    if height and not width:
        ratio = height / original_height
        return max(1, round(original_width * ratio)), height

    if width and height:
        ratio = min(width / original_width, height / original_height)
        return max(1, round(original_width * ratio)), max(1, round(original_height * ratio))

    return original_width, original_height