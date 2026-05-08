from urllib.parse import urlencode

from django.core import signing
from django.utils import timezone


PROCESSING_JOB_ACCESS_SALT = "processing-job-access"
PROCESSING_JOB_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7


def generate_processing_job_access_token(job):
    return signing.dumps(
        {"job_id": str(job.id)},
        salt=PROCESSING_JOB_ACCESS_SALT,
    )


def is_processing_job_token_valid(job, token):
    if not token:
        return False

    try:
        payload = signing.loads(
            token,
            salt=PROCESSING_JOB_ACCESS_SALT,
            max_age=PROCESSING_JOB_TOKEN_MAX_AGE_SECONDS,
        )
    except signing.BadSignature:
        return False
    except signing.SignatureExpired:
        return False

    if payload.get("job_id") != str(job.id):
        return False

    if job.expires_at and timezone.now() > job.expires_at:
        return False

    return True


def build_processing_job_url(url, token=None):
    if not token:
        return url

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode({'token': token})}"
