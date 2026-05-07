from pathlib import Path

from PIL import Image, UnidentifiedImageError

from apps.converters.exceptions import InvalidFileError, UnsupportedConversionError


SUPPORTED_OUTPUT_FORMATS = {"jpeg", "jpg", "png", "webp"}


def normalize_format(value: str) -> str:
    value = value.lower().strip()

    if value == "jpg":
        return "jpeg"

    return value


def convert_image_file(
    *,
    input_path: str,
    output_path: str,
    output_format: str,
    quality: int = 85,
    background: str = "#ffffff",
) -> str:
    input_path = Path(input_path)
    output_path = Path(output_path)

    output_format = normalize_format(output_format)

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise UnsupportedConversionError(
            f"Format de sortie non supporté : {output_format}"
        )

    try:
        with Image.open(input_path) as image:
            image.load()

            if output_format == "jpeg":
                image = prepare_for_jpeg(image, background)
            elif output_format == "png":
                image = image.convert("RGBA")
            elif output_format == "webp":
                image = image.convert("RGBA")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            save_kwargs = {}

            if output_format in {"jpeg", "webp"}:
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True

            image.save(
                output_path,
                format="JPEG" if output_format == "jpeg" else output_format.upper(),
                **save_kwargs,
            )

    except UnidentifiedImageError as exc:
        raise InvalidFileError("Image invalide ou corrompue.") from exc
    except OSError as exc:
        raise InvalidFileError("Impossible de lire ou convertir cette image.") from exc

    return str(output_path)


def prepare_for_jpeg(image: Image.Image, background: str) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        background_image = Image.new("RGB", image.size, background)
        rgba = image.convert("RGBA")
        background_image.paste(rgba, mask=rgba.getchannel("A"))
        return background_image

    return image.convert("RGB")