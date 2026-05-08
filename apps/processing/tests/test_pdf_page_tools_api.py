from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.processing.models import ProcessingJob, ProcessingStatus, ProcessingTool


class PdfPageToolsApiTests(APITestCase):
    def _build_job(self, *, tool, options):
        return ProcessingJob.objects.create(
            user=None,
            tool=tool,
            status=ProcessingStatus.COMPLETED,
            original_filename="input.pdf",
            options=options,
        )

    @patch("apps.processing.views.run_pdf_delete_pages_job")
    def test_pdf_delete_pages_creates_anonymous_tracked_job(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_DELETE_PAGES,
            options={"pages": "2,4"},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-delete-pages"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "pages": "2,4",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_DELETE_PAGES)
        self.assertEqual(run_job_mock.call_args.kwargs["options"], {"pages": "2,4"})
        self.assertIn(str(job.id), self.client.session["processing_job_ids"])

    def test_pdf_delete_pages_requires_pages_expression(self):
        response = self.client.post(
            reverse("processing:pdf-delete-pages"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Veuillez préciser les pages à supprimer.",
        )

    @patch("apps.processing.views.run_pdf_extract_pages_job")
    def test_pdf_extract_pages_passes_requested_pages(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_EXTRACT_PAGES,
            options={"pages": "3,1"},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-extract-pages"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "pages": "3,1",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_EXTRACT_PAGES)
        self.assertEqual(run_job_mock.call_args.kwargs["options"], {"pages": "3,1"})

    @patch("apps.processing.views.run_pdf_organize_job")
    def test_pdf_organize_accepts_order_parameter(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_ORGANIZE,
            options={"pages": "3,1,2"},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-organize"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "order": "3,1,2",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_ORGANIZE)
        self.assertEqual(run_job_mock.call_args.kwargs["options"], {"pages": "3,1,2"})

    @patch("apps.processing.views.run_pdf_rotate_custom_job")
    def test_pdf_rotate_custom_accepts_rotations_expression(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_ROTATE_CUSTOM,
            options={"rotations": "1:90,3:270"},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-rotate-custom"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "rotations": "1:90,3:270",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_ROTATE_CUSTOM)
        self.assertEqual(
            run_job_mock.call_args.kwargs["options"],
            {"rotations": "1:90,3:270"},
        )

    def test_pdf_add_blank_page_requires_target_page_for_before_after(self):
        response = self.client.post(
            reverse("processing:pdf-add-blank-page"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "position": "after",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Veuillez préciser la page cible pour l'insertion.",
        )

    @patch("apps.processing.views.run_pdf_add_blank_page_job")
    def test_pdf_add_blank_page_accepts_end_position_without_page(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_ADD_BLANK_PAGE,
            options={"position": "end"},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-add-blank-page"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "position": "end",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_ADD_BLANK_PAGE)
        self.assertEqual(run_job_mock.call_args.kwargs["options"]["position"], "end")

    @patch("apps.processing.views.run_pdf_reverse_pages_job")
    def test_pdf_reverse_pages_creates_job(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_REVERSE_PAGES,
            options={},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-reverse-pages"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                )
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_REVERSE_PAGES)
