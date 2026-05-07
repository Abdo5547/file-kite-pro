import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.converters.exceptions import ConverterError
from apps.processing.models import ProcessingJob, ProcessingStatus, ProcessingTool


class ProcessingJobAccessApiTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        self.other_user = user_model.objects.create_user(
            email="other@example.com",
            password="testpass123",
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()
        super().tearDown()

    def _create_job(self, *, user=None, status_value=ProcessingStatus.PENDING, with_output=False):
        job = ProcessingJob.objects.create(
            user=user,
            tool=ProcessingTool.PDF_MERGE,
            status=status_value,
            original_filename="input.pdf",
        )

        if with_output:
            job.output_file.save(
                "result.pdf",
                ContentFile(b"%PDF-1.4\n% test file\n"),
                save=True,
            )

        return job

    def test_authenticated_user_can_access_own_job_detail(self):
        job = self._create_job(user=self.user)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(job.id))

    def test_authenticated_user_cannot_access_another_users_job_detail(self):
        job = self._create_job(user=self.other_user)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Vous n'avez pas accès à ce job.")

    def test_anonymous_user_can_access_session_tracked_job_detail(self):
        job = self._create_job()
        session = self.client.session
        session["processing_job_ids"] = [str(job.id)]
        session.save()

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(job.id))

    def test_anonymous_user_cannot_access_untracked_job_detail(self):
        job = self._create_job()

        response = self.client.get(
            reverse("processing:job-detail", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Vous n'avez pas accès à ce job.")

    def test_authenticated_user_can_download_own_completed_job(self):
        job = self._create_job(
            user=self.user,
            status_value=ProcessingStatus.COMPLETED,
            with_output=True,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("processing:job-download", kwargs={"job_id": job.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("result.pdf", response["Content-Disposition"])

    @patch("apps.processing.views.run_pdf_merge_job")
    def test_pdf_merge_error_does_not_expose_unrelated_job_metadata(self, run_pdf_merge_job_mock):
        run_pdf_merge_job_mock.side_effect = ConverterError("Fusion impossible.")
        self._create_job(user=self.other_user, status_value=ProcessingStatus.FAILED)

        response = self.client.post(
            reverse("processing:pdf-merge"),
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Fusion impossible.")
        self.assertNotIn("job", response.data)
