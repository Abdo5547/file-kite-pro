import tempfile
from pathlib import Path
from unittest import TestCase

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError
from apps.converters.pdf.add_attachments import add_attachments_to_pdf_file
from apps.converters.pdf.add_blank_page import add_blank_page_to_pdf_file
from apps.converters.pdf.alternate_merge import alternate_merge_pdf_files
from apps.converters.pdf.combine_single_page import combine_pdf_into_single_page_file
from apps.converters.pdf.delete_pages import delete_pdf_pages_file
from apps.converters.pdf.divide_pages import divide_pdf_pages_file
from apps.converters.pdf.extract_attachments import extract_pdf_attachments
from apps.converters.pdf.extract_pages import extract_pdf_pages_file
from apps.converters.pdf.grid_combine import grid_combine_pdf_file, n_up_pdf_file
from apps.converters.pdf.multi_tool import run_pdf_multi_tool_file
from apps.converters.pdf.organize import organize_pdf_file
from apps.converters.pdf.posterize_pdf import posterize_pdf_file
from apps.converters.pdf.reverse_pages import reverse_pdf_pages_file
from apps.converters.pdf.rotate_custom import rotate_custom_pdf_file


class PdfPageToolsConverterTests(TestCase):
    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()
        super().tearDown()

    def _create_pdf(
        self,
        page_count=4,
        *,
        base_width=200,
        base_height=300,
        filename="input.pdf",
    ):
        input_path = self.temp_path / filename
        writer = PdfWriter()
        for index in range(page_count):
            writer.add_blank_page(width=base_width + index, height=base_height + index)
        with input_path.open("wb") as output_file:
            writer.write(output_file)
        return input_path

    def test_delete_pdf_pages_file_removes_selected_pages(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "deleted.pdf"
        delete_pdf_pages_file(
            input_path=str(input_path),
            output_path=str(output_path),
            pages_expression="2,4",
        )
        reader = PdfReader(str(output_path))
        widths = [float(page.mediabox.width) for page in reader.pages]
        self.assertEqual(len(reader.pages), 2)
        self.assertEqual(widths, [200.0, 202.0])

    def test_extract_pdf_pages_file_preserves_requested_order(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "extracted.pdf"
        extract_pdf_pages_file(
            input_path=str(input_path),
            output_path=str(output_path),
            pages_expression="3,1",
        )
        reader = PdfReader(str(output_path))
        widths = [float(page.mediabox.width) for page in reader.pages]
        self.assertEqual(widths, [202.0, 200.0])

    def test_organize_pdf_file_reorders_all_pages(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "organized.pdf"
        organize_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            page_order_expression="4,2,1,3",
        )
        reader = PdfReader(str(output_path))
        widths = [float(page.mediabox.width) for page in reader.pages]
        self.assertEqual(widths, [203.0, 201.0, 200.0, 202.0])

    def test_organize_pdf_file_requires_each_page_once(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "organized.pdf"
        with self.assertRaises(InvalidFileError):
            organize_pdf_file(
                input_path=str(input_path),
                output_path=str(output_path),
                page_order_expression="3,1,2",
            )

    def test_rotate_custom_pdf_file_rotates_selected_pages(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "rotated_custom.pdf"
        rotate_custom_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            rotations_expression="1:90,3:270",
        )
        reader = PdfReader(str(output_path))
        rotations = [int(page.get("/Rotate", 0)) for page in reader.pages]
        self.assertEqual(rotations, [90, 0, 270, 0])

    def test_add_blank_page_to_pdf_file_inserts_page_after_target(self):
        input_path = self._create_pdf(page_count=3)
        output_path = self.temp_path / "blank_added.pdf"
        add_blank_page_to_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            position="after",
            page_number=1,
        )
        reader = PdfReader(str(output_path))
        dimensions = [
            (float(page.mediabox.width), float(page.mediabox.height))
            for page in reader.pages
        ]
        self.assertEqual(len(reader.pages), 4)
        self.assertEqual(dimensions[1], dimensions[0])

    def test_reverse_pdf_pages_file_reverses_page_order(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "reversed.pdf"
        reverse_pdf_pages_file(input_path=str(input_path), output_path=str(output_path))
        reader = PdfReader(str(output_path))
        widths = [float(page.mediabox.width) for page in reader.pages]
        self.assertEqual(widths, [203.0, 202.0, 201.0, 200.0])

    def test_n_up_pdf_file_groups_pages_on_single_sheet(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "n_up.pdf"
        n_up_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            pages_per_sheet=4,
        )
        reader = PdfReader(str(output_path))
        self.assertEqual(len(reader.pages), 1)
        self.assertEqual(float(reader.pages[0].mediabox.width), 406.0)
        self.assertEqual(float(reader.pages[0].mediabox.height), 606.0)

    def test_grid_combine_pdf_file_uses_requested_grid(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "grid.pdf"
        grid_combine_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            rows=1,
            columns=2,
        )
        reader = PdfReader(str(output_path))
        self.assertEqual(len(reader.pages), 2)
        self.assertEqual(float(reader.pages[0].mediabox.width), 406.0)
        self.assertEqual(float(reader.pages[0].mediabox.height), 303.0)

    def test_alternate_merge_pdf_files_interleaves_two_documents(self):
        first_path = self._create_pdf(page_count=3, base_width=200, filename="first.pdf")
        second_path = self._create_pdf(page_count=2, base_width=400, filename="second.pdf")
        output_path = self.temp_path / "alternate.pdf"
        alternate_merge_pdf_files(
            input_paths=[str(first_path), str(second_path)],
            output_path=str(output_path),
        )
        reader = PdfReader(str(output_path))
        widths = [float(page.mediabox.width) for page in reader.pages]
        self.assertEqual(widths, [200.0, 400.0, 201.0, 401.0, 202.0])

    def test_divide_pdf_pages_file_vertical_creates_two_pages_per_page(self):
        input_path = self._create_pdf(page_count=1, base_width=200, base_height=300)
        output_path = self.temp_path / "divided.pdf"
        divide_pdf_pages_file(
            input_path=str(input_path),
            output_path=str(output_path),
            mode="vertical",
        )
        reader = PdfReader(str(output_path))
        self.assertEqual(len(reader.pages), 2)
        self.assertEqual(float(reader.pages[0].mediabox.width), 100.0)
        self.assertEqual(float(reader.pages[0].mediabox.height), 300.0)

    def test_combine_pdf_into_single_page_file_stacks_pages_vertically(self):
        input_path = self._create_pdf(page_count=2, base_width=200, base_height=300)
        output_path = self.temp_path / "single_page.pdf"
        combine_pdf_into_single_page_file(
            input_path=str(input_path),
            output_path=str(output_path),
            gap=10,
        )
        reader = PdfReader(str(output_path))
        self.assertEqual(len(reader.pages), 1)
        self.assertEqual(float(reader.pages[0].mediabox.width), 201.0)
        self.assertEqual(float(reader.pages[0].mediabox.height), 611.0)

    def test_posterize_pdf_file_creates_tiles(self):
        input_path = self._create_pdf(page_count=1, base_width=200, base_height=300)
        output_path = self.temp_path / "posterized.pdf"
        posterize_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            rows=2,
            columns=2,
        )
        reader = PdfReader(str(output_path))
        self.assertEqual(len(reader.pages), 4)
        self.assertEqual(float(reader.pages[0].mediabox.width), 100.0)
        self.assertEqual(float(reader.pages[0].mediabox.height), 150.0)

    def test_add_attachments_to_pdf_file_embeds_files(self):
        input_path = self._create_pdf(page_count=1)
        output_path = self.temp_path / "attached.pdf"
        attachment_path = self.temp_path / "note.txt"
        attachment_path.write_text("hello", encoding="utf-8")

        add_attachments_to_pdf_file(
            input_path=str(input_path),
            output_path=str(output_path),
            attachment_paths=[str(attachment_path)],
        )

        reader = PdfReader(str(output_path))
        attachments = list(reader.attachment_list)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].name, "note.txt")
        self.assertEqual(attachments[0].content, b"hello")

    def test_extract_pdf_attachments_returns_written_files(self):
        input_path = self.temp_path / "embedded.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=300)
        writer.add_attachment("note.txt", b"hello")
        writer.add_attachment("data.bin", b"abc")
        with input_path.open("wb") as output_file:
            writer.write(output_file)

        output_dir = self.temp_path / "attachments"
        extracted_files = extract_pdf_attachments(
            input_path=str(input_path),
            output_dir=str(output_dir),
        )

        self.assertEqual(sorted(Path(path).name for path in extracted_files), ["data.bin", "note.txt"])
        self.assertEqual((output_dir / "note.txt").read_bytes(), b"hello")
        self.assertEqual((output_dir / "data.bin").read_bytes(), b"abc")

    def test_run_pdf_multi_tool_file_applies_multiple_operations(self):
        input_path = self._create_pdf(page_count=4)
        output_path = self.temp_path / "multi_tool.pdf"

        run_pdf_multi_tool_file(
            input_path=str(input_path),
            output_path=str(output_path),
            operations=[
                {"tool": "delete-pages", "pages": "2"},
                {"tool": "reverse-pages"},
            ],
        )

        reader = PdfReader(str(output_path))
        widths = [float(page.mediabox.width) for page in reader.pages]
        self.assertEqual(widths, [203.0, 202.0, 200.0])
