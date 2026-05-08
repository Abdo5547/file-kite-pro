import tempfile
from pathlib import Path
from unittest import TestCase

from pypdf import PdfReader, PdfWriter

from apps.converters.exceptions import InvalidFileError
from apps.converters.pdf.delete_pages import delete_pdf_pages_file
from apps.converters.pdf.extract_pages import extract_pdf_pages_file
from apps.converters.pdf.organize import organize_pdf_file


class PdfPageToolsConverterTests(TestCase):
    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()
        super().tearDown()

    def _create_pdf(self, page_count=4):
        input_path = self.temp_path / "input.pdf"
        writer = PdfWriter()

        for index in range(page_count):
            writer.add_blank_page(width=200 + index, height=300)

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
