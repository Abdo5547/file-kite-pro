from pathlib import Path

from PIL import Image, UnidentifiedImageError

from apps.converters.exceptions import InvalidFileError
from apps.converters.images.convert import normalize_format, prepare_for_jpeg


def compress_image_file(
    *,
    input_path: str,
    output_path: str,
    output_format: str = "webp",
    quality: int = 75,
    background: str = "#ffffff",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    output_format = normalize_format(output_format)

    try:
        with Image.open(input_path) as image:
            image.load()

            if output_format == "jpeg":
                image = prepare_for_jpeg(image, background)
            elif output_format in {"png", "webp"}:
                image = image.convert("RGBA")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            save_kwargs = {"optimize": True}

            if output_format in {"jpeg", "webp"}:
                save_kwargs["quality"] = int(quality)

            if output_format == "png":
                save_kwargs["compress_level"] = 9

            image.save(
                output_path,
                format="JPEG" if output_format == "jpeg" else output_format.upper(),
                **save_kwargs,
            )

    except UnidentifiedImageError as exc:
        raise InvalidFileError("Image invalide ou corrompue.") from exc
    except OSError as exc:
        raise InvalidFileError("Impossible de compresser cette image.") from exc

    return str(output_path)