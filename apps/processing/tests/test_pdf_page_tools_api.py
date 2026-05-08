import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
        job = self._build_job(tool=ProcessingTool.PDF_REVERSE_PAGES, options={})
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

    @patch("apps.processing.views.run_pdf_n_up_job")
    def test_pdf_n_up_passes_pages_per_sheet(self, run_job_mock):
        job = self._build_job(tool=ProcessingTool.PDF_N_UP, options={"pages_per_sheet": 4})
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-n-up"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "pages_per_sheet": "4",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_N_UP)
        self.assertEqual(
            run_job_mock.call_args.kwargs["options"],
            {"pages_per_sheet": "4"},
        )

    @patch("apps.processing.views.run_pdf_grid_combine_job")
    def test_pdf_grid_combine_passes_grid_dimensions(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_GRID_COMBINE,
            options={"rows": 2, "columns": 3},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-grid-combine"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "rows": "2",
                "columns": "3",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_GRID_COMBINE)
        self.assertEqual(
            run_job_mock.call_args.kwargs["options"],
            {"rows": "2", "columns": "3"},
        )

    def test_pdf_alternate_merge_requires_two_files(self):
        response = self.client.post(
            reverse("processing:pdf-alternate-merge"),
            data={
                "files": [
                    SimpleUploadedFile(
                        "first.pdf",
                        b"%PDF-1.4\ntest\n",
                        content_type="application/pdf",
                    )
                ]
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Veuillez envoyer exactement deux fichiers PDF avec le champ 'files'.",
        )

    @patch("apps.processing.views.run_pdf_alternate_merge_job")
    def test_pdf_alternate_merge_creates_job(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_ALTERNATE_MERGE,
            options={"file_count": 2},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-alternate-merge"),
            data={
                "files": [
                    SimpleUploadedFile(
                        "first.pdf",
                        b"%PDF-1.4\nfirst\n",
                        content_type="application/pdf",
                    ),
                    SimpleUploadedFile(
                        "second.pdf",
                        b"%PDF-1.4\nsecond\n",
                        content_type="application/pdf",
                    ),
                ]
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_ALTERNATE_MERGE)

    @patch("apps.processing.views.run_pdf_divide_pages_job")
    def test_pdf_divide_pages_passes_mode(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_DIVIDE_PAGES,
            options={"mode": "quarters"},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-divide-pages"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "mode": "quarters",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_DIVIDE_PAGES)
        self.assertEqual(run_job_mock.call_args.kwargs["options"], {"mode": "quarters"})

    @patch("apps.processing.views.run_pdf_combine_single_page_job")
    def test_pdf_combine_single_page_passes_gap(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_COMBINE_SINGLE_PAGE,
            options={"gap": 12},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-combine-single-page"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "gap": "12",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_COMBINE_SINGLE_PAGE)
        self.assertEqual(run_job_mock.call_args.kwargs["options"], {"gap": "12"})

    @patch("apps.processing.views.run_pdf_posterize_job")
    def test_pdf_posterize_passes_grid(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_POSTERIZE,
            options={"rows": 2, "columns": 2},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-posterize"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "rows": "2",
                "columns": "2",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_POSTERIZE)
        self.assertEqual(
            run_job_mock.call_args.kwargs["options"],
            {"rows": "2", "columns": "2"},
        )

    def test_pdf_add_attachments_requires_attachment_files(self):
        response = self.client.post(
            reverse("processing:pdf-add-attachments"),
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
            "Veuillez envoyer au moins un fichier joint avec le champ 'attachments'.",
        )

    @patch("apps.processing.views.run_pdf_add_attachments_job")
    def test_pdf_add_attachments_creates_job(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_ADD_ATTACHMENTS,
            options={"attachment_count": 1},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-add-attachments"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "attachments": [
                    SimpleUploadedFile(
                        "note.txt",
                        b"hello",
                        content_type="text/plain",
                    )
                ],
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_ADD_ATTACHMENTS)
        self.assertEqual(len(run_job_mock.call_args.kwargs["attachment_files"]), 1)

    @patch("apps.processing.views.run_pdf_extract_attachments_job")
    def test_pdf_extract_attachments_creates_job(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_EXTRACT_ATTACHMENTS,
            options={},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-extract-attachments"),
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
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_EXTRACT_ATTACHMENTS)

    def test_pdf_multi_tool_requires_valid_json(self):
        response = self.client.post(
            reverse("processing:pdf-multi-tool"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "operations": "not-json",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Le champ 'operations' doit contenir un JSON valide.",
        )

    @patch("apps.processing.views.run_pdf_multi_tool_job")
    def test_pdf_multi_tool_passes_operations_and_attachments(self, run_job_mock):
        job = self._build_job(
            tool=ProcessingTool.PDF_MULTI_TOOL,
            options={"operations": [{"tool": "delete-pages", "pages": "2"}]},
        )
        run_job_mock.return_value = job

        response = self.client.post(
            reverse("processing:pdf-multi-tool"),
            data={
                "file": SimpleUploadedFile(
                    "input.pdf",
                    b"%PDF-1.4\ntest\n",
                    content_type="application/pdf",
                ),
                "operations": json.dumps([
                    {"tool": "delete-pages", "pages": "2"},
                    {"tool": "add-attachments"},
                ]),
                "attachments": [
                    SimpleUploadedFile(
                        "note.txt",
                        b"hello",
                        content_type="text/plain",
                    )
                ],
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tool"], ProcessingTool.PDF_MULTI_TOOL)
        self.assertEqual(
            run_job_mock.call_args.kwargs["options"]["operations"],
            [
                {"tool": "delete-pages", "pages": "2"},
                {"tool": "add-attachments"},
            ],
        )
        self.assertEqual(len(run_job_mock.call_args.kwargs["attachment_files"]), 1)
