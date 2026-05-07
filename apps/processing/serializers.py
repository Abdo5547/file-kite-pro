from django.urls import reverse
from rest_framework import serializers

from .models import ProcessingJob


class ProcessingJobSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

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
            "created_at",
            "completed_at",
            "expires_at",
        )

    def get_download_url(self, obj):
        if not obj.output_file:
            return None

        request = self.context.get("request")

        url = reverse(
            "processing:job-download",
            kwargs={"job_id": obj.id},
        )

        if request:
            return request.build_absolute_uri(url)

        return url