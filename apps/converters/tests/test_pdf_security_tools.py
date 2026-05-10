import tempfile
import unittest
from pathlib import Path

import fitz
from pypdf import PdfReader, PdfWriter

from apps.converters.pdf.decrypt import decrypt_pdf_file
from apps.converters.pdf.encrypt import encrypt_pdf_file
from apps.converters.pdf.metadata import remove_pdf_metadata
from apps.converters.pdf.permissions import change_pdf_permissions
from apps.converters.pdf.redact import find_and_redact_text_in_pdf
from apps.converters.pdf.sanitize import sanitize_pdf_file


class PdfSecurityToolsTests(unittest.TestCase):
    def test_encrypt_then_decrypt_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source = temp_dir_path / "source.pdf"
            encrypted = temp_dir_path / "encrypted.pdf"
            decrypted = temp_dir_path / "decrypted.pdf"

            _create_simple_pdf(source, "hello pdf")

            encrypt_pdf_file(
                input_path=str(source),
                output_path=str(encrypted),
                user_password="1234",
            )
            self.assertTrue(PdfReader(str(encrypted)).is_encrypted)

            decrypt_pdf_file(
                input_path=str(encrypted),
                output_path=str(decrypted),
                password="1234",
            )
            self.assertFalse(PdfReader(str(decrypted)).is_encrypted)

    def test_remove_pdf_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source = temp_dir_path / "source.pdf"
            cleaned = temp_dir_path / "cleaned.pdf"

            writer = PdfWriter()
            writer.add_blank_page(width=300, height=300)
            writer.add_metadata({"/Title": "Secret", "/Author": "FileKit"})
            with source.open("wb") as output_file:
                writer.write(output_file)

            remove_pdf_metadata(
                input_path=str(source),
                output_path=str(cleaned),
            )

            metadata = PdfReader(str(cleaned)).metadata
            self.assertNotIn("/Title", metadata)
            self.assertNotIn("/Author", metadata)

    def test_sanitize_pdf_removes_javascript(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source = temp_dir_path / "source.pdf"
            cleaned = temp_dir_path / "cleaned.pdf"

            writer = PdfWriter()
            writer.add_blank_page(width=300, height=300)
            writer.add_js("app.alert('hello')")
            with source.open("wb") as output_file:
                writer.write(output_file)

            sanitize_pdf_file(
                input_path=str(source),
                output_path=str(cleaned),
            )

            reader = PdfReader(str(cleaned))
            root = reader.trailer["/Root"]
            self.assertNotIn("/OpenAction", root)

    def test_change_pdf_permissions_encrypts_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source = temp_dir_path / "source.pdf"
            secured = temp_dir_path / "secured.pdf"

            _create_simple_pdf(source, "permissions")

            change_pdf_permissions(
                input_path=str(source),
                output_path=str(secured),
                user_password="user",
                owner_password="owner",
                allowed_permissions=["print"],
            )

            self.assertTrue(PdfReader(str(secured)).is_encrypted)

    def test_find_and_redact_text_in_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source = temp_dir_path / "source.pdf"
            redacted = temp_dir_path / "redacted.pdf"

            _create_simple_pdf(source, "secret phrase")

            find_and_redact_text_in_pdf(
                input_path=str(source),
                output_path=str(redacted),
                search_text="secret",
            )

            self.assertTrue(redacted.exists())
            document = fitz.open(str(redacted))
            try:
                text = "".join(page.get_text() for page in document)
                self.assertNotIn("secret", text.lower())
            finally:
                document.close()


def _create_simple_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), text)
        document.save(str(path))
    finally:
        document.close()
