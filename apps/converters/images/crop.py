from pathlib import Path

from PIL import Image, UnidentifiedImageError

from apps.converters.exceptions import InvalidFileError, ProcessingLimitError
from apps.converters.images.convert import normalize_format, prepare_for_jpeg


SUPPORTED_OUTPUT_FORMATS = {"jpeg", "png", "webp"}
MAX_IMAGE_DIMENSION = 10000


def crop_image_file(
    *,
    input_path: str,
    output_path: str,
    x: int,
    y: int,
    width: int,
    height: int,
    output_format: str = "webp",
    quality: int = 85,
    background: str = "#ffffff",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    output_format = normalize_format(output_format)

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise InvalidFileError(f"Format de sortie non supporte : {output_format}")

    if x < 0 or y < 0:
        raise InvalidFileError("Les coordonnees de recadrage doivent etre positives.")

    if width <= 0 or height <= 0:
        raise InvalidFileError("La largeur et la hauteur du recadrage doivent etre superieures a 0.")

    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ProcessingLimitError(
            f"Le recadrage ne peut pas depasser {MAX_IMAGE_DIMENSION}px sur un axe."
        )

    try:
        with Image.open(input_path) as image:
            image.load()

            image_width, image_height = image.size
            right = x + width
            bottom = y + height

            if x >= image_width or y >= image_height:
                raise InvalidFileError("La zone de recadrage commence en dehors de l'image.")

            if right > image_width or bottom > image_height:
                raise InvalidFileError("La zone de recadrage depasse les limites de l'image.")

            result = image.crop((x, y, right, bottom))

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
        raise InvalidFileError("Impossible de recadrer cette image.") from exc

    return str(output_path)
