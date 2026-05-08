from django.urls import reverse
from rest_framework import serializers

from .access import build_processing_job_url, generate_processing_job_access_token
from .models import ProcessingJob


class ProcessingJobSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    access_token = serializers.SerializerMethodField()

    class Meta:
        model = ProcessingJob
        fields = (
            "id",
            "tool",
            "status",
            "original_filename",
            "input_size",
            "output_size",
            "options",
            "error_message",
            "download_url",
            "access_token",
            "created_at",
            "completed_at",
            "expires_at",
        )

    def get_access_token(self, obj):
        if obj.user_id:
            return None

        return generate_processing_job_access_token(obj)

    def get_download_url(self, obj):
        if not obj.output_file:
            return None

        request = self.context.get("request")
        url = reverse(
            "processing:job-download",
            kwargs={"job_id": obj.id},
        )

        token = self.get_access_token(obj)

        if request:
            url = request.build_absolute_uri(url)

        return build_processing_job_url(url, token=token)
