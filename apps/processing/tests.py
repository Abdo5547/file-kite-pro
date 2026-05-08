from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User

from .access import generate_processing_job_access_token
from .models import ProcessingJob, ProcessingStatus, ProcessingTool


class ProcessingJobAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="secret123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="secret123",
        )

    def test_guest_job_detail_requires_token(self):
        job = ProcessingJob.objects.create(
            tool=ProcessingTool.PDF_MERGE,
            status=ProcessingStatus.PENDING,
        )

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, 404)

    def test_guest_job_detail_accepts_signed_token(self):
        job = ProcessingJob.objects.create(
            tool=ProcessingTool.PDF_MERGE,
            status=ProcessingStatus.PENDING,
        )
        token = generate_processing_job_access_token(job)

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id}),
            {"token": token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data["id"]), str(job.id))
        self.assertEqual(response.data["access_token"], token)

    def test_job_detail_allows_owner_without_token(self):
        job = ProcessingJob.objects.create(
            user=self.owner,
            tool=ProcessingTool.PDF_MERGE,
            status=ProcessingStatus.PENDING,
        )
        self.client.force_authenticate(self.owner)

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, 200)

    def test_job_detail_hides_other_user_job(self):
        job = ProcessingJob.objects.create(
            user=self.owner,
            tool=ProcessingTool.PDF_MERGE,
            status=ProcessingStatus.PENDING,
        )
        self.client.force_authenticate(self.other_user)

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, 404)

    def test_guest_job_download_requires_token(self):
        job = ProcessingJob.objects.create(
            tool=ProcessingTool.PDF_MERGE,
            status=ProcessingStatus.COMPLETED,
        )
        job.output_file.save(
            "result.pdf",
            SimpleUploadedFile("result.pdf", b"%PDF-1.4\n", content_type="application/pdf"),
        )

        response = self.client.get(
            reverse("processing:job-download", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, 404)


class ProcessingEndpointHardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.processing.secure_views.enqueue_pdf_to_images_job")
    def test_pdf_to_images_does_not_leak_internal_errors(self, mocked_enqueue):
        mocked_enqueue.side_effect = RuntimeError("boom")
        upload = SimpleUploadedFile(
            "sample.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("processing:pdf-to-images"),
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data["detail"],
            "Une erreur serveur est survenue pendant la conversion PDF vers images.",
        )
        self.assertNotIn("error", response.data)
        self.assertNotIn("type", response.data)

    @patch("apps.processing.secure_views.process_pdf_merge_job.delay")
    def test_pdf_merge_async_rejects_fake_pdf_payload(self, mocked_delay):
        upload_one = SimpleUploadedFile(
            "fake-1.pdf",
            b"not-a-real-pdf",
            content_type="application/pdf",
        )
        upload_two = SimpleUploadedFile(
            "fake-2.pdf",
            b"still-not-a-real-pdf",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("processing:pdf-merge-async"),
            {"files": [upload_one, upload_two]},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)
        mocked_delay.assert_not_called()

    @patch("apps.processing.secure_views.process_pdf_merge_job.delay")
    def test_pdf_merge_async_returns_serialized_job_with_guest_token(self, mocked_delay):
        upload_one = SimpleUploadedFile(
            "valid-1.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n",
            content_type="application/pdf",
        )
        upload_two = SimpleUploadedFile(
            "valid-2.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("processing:pdf-merge-async"),
            {"files": [upload_one, upload_two]},
            format="multipart",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["status"], ProcessingStatus.PENDING)
        self.assertIn("access_token", response.data)
        self.assertIsNotNone(response.data["access_token"])
        mocked_delay.assert_called_once()
