from pathlib import Path

from apps.converters.images.rotate import rotate_flip_image_file


def rotate_images_batch(
    *,
    input_paths: list[str],
    output_dir: str,
    operation: str,
    output_format: str = "webp",
    quality: int = 85,
    background: str = "#ffffff",
) -> list[str]:
    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    output_paths: list[str] = []
    output_extension = "jpg" if output_format == "jpeg" else output_format

    for index, input_path in enumerate(input_paths, start=1):
        input_file_path = Path(input_path)
        source_stem = input_file_path.stem or f"image_{index}"
        output_path = output_directory / f"{source_stem}_{operation}.{output_extension}"

        rotate_flip_image_file(
            input_path=str(input_file_path),
            output_path=str(output_path),
            operation=operation,
            output_format=output_format,
            quality=quality,
            background=background,
        )

        output_paths.append(str(output_path))

    return output_paths
