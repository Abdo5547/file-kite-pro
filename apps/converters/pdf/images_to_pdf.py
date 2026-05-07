from pathlib import Path

from PIL import Image, UnidentifiedImageError

from apps.converters.exceptions import InvalidFileError


def images_to_pdf_file(
    *,
    input_paths: list[str],
    output_path: str,
    page_size: str = "auto",
    orientation: str = "portrait",
    background: str = "#ffffff",
) -> str:
    if not input_paths:
        raise InvalidFileError("Veuillez fournir au moins une image.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf_images = []

    try:
        for input_path in input_paths:
            image_path = Path(input_path)

            with Image.open(image_path) as image:
                image.load()

                prepared = prepare_image_for_pdf(
                    image=image,
                    page_size=page_size,
                    orientation=orientation,
                    background=background,
                )

                pdf_images.append(prepared)

        if not pdf_images:
            raise InvalidFileError("Aucune image valide à convertir.")

        first_image = pdf_images[0]
        other_images = pdf_images[1:]

        first_image.save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=other_images,
        )

    except UnidentifiedImageError as exc:
        raise InvalidFileError("Une image est invalide ou corrompue.") from exc
    except OSError as exc:
        raise InvalidFileError("Impossible de convertir les images en PDF.") from exc

    return str(output_path)


def prepare_image_for_pdf(
    *,
    image: Image.Image,
    page_size: str,
    orientation: str,
    background: str,
) -> Image.Image:
    image = image.convert("RGBA")

    if page_size == "auto":
        canvas = Image.new("RGB", image.size, background)
        canvas.paste(image, mask=image.getchannel("A"))
        return canvas

    page_width, page_height = get_page_dimensions(page_size)

    if orientation == "landscape":
        page_width, page_height = page_height, page_width

    canvas = Image.new("RGB", (page_width, page_height), background)

    image.thumbnail(
        (page_width, page_height),
        Image.Resampling.LANCZOS,
    )

    x = (page_width - image.width) // 2
    y = (page_height - image.height) // 2

    canvas.paste(image, (x, y), mask=image.getchannel("A"))

    return canvas


def get_page_dimensions(page_size: str) -> tuple[int, int]:
    page_size = page_size.lower().strip()

    sizes = {
        "a4": (1240, 1754),
        "letter": (1275, 1650),
        "square": (1500, 1500),
    }

    if page_size not in sizes:
        raise InvalidFileError(
            "Taille de page non supportée. Utilisez auto, a4, letter ou square."
        )

    return sizes[page_size]