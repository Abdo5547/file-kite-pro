import tempfile
import unittest
from pathlib import Path

from PIL import Image

from apps.converters.images.batch_rotate import rotate_images_batch
from apps.converters.images.crop import crop_image_file


class ImageExtraToolsTests(unittest.TestCase):
    def test_crop_image_file_creates_expected_size(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_path = temp_dir_path / "input.png"
            output_path = temp_dir_path / "cropped.webp"

            Image.new("RGBA", (120, 80), "#336699").save(input_path)

            crop_image_file(
                input_path=str(input_path),
                output_path=str(output_path),
                x=10,
                y=5,
                width=40,
                height=20,
            )

            self.assertTrue(output_path.exists())

            with Image.open(output_path) as image:
                self.assertEqual(image.size, (40, 20))

    def test_rotate_images_batch_creates_multiple_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            input_one = temp_dir_path / "one.png"
            input_two = temp_dir_path / "two.png"
            output_dir = temp_dir_path / "output"

            Image.new("RGBA", (90, 40), "#aa5500").save(input_one)
            Image.new("RGBA", (60, 30), "#0055aa").save(input_two)

            output_paths = rotate_images_batch(
                input_paths=[str(input_one), str(input_two)],
                output_dir=str(output_dir),
                operation="rotate_90",
            )

            self.assertEqual(len(output_paths), 2)

            for output_path in output_paths:
                self.assertTrue(Path(output_path).exists())
