from urllib.parse import urlparse

import requests
from rest_framework import serializers

from core.config import application_config


def send_email(
    emails: list[str], subject: str, content: str, fail_silently: bool = True
) -> bool:
    api_key: str = application_config.MAILGUN_API_KEY or ""
    domain: str = application_config.MAILGUN_DOMAIN or ""

    url = "https://api.mailgun.net/v3/" + domain + "/messages"
    data = {
        "from": f"no.reply@{domain}",
        "to": emails,
        "subject": subject,
        "html": content,
    }

    response = requests.post(url, data=data, auth=("api", api_key))
    if not fail_silently:
        response.raise_for_status()

    return response.ok


class EmptySerializer(serializers.Serializer):
    pass


def extract_base_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.hostname:
            return None
        netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
        return f"{parsed.scheme}://{netloc}"
    except Exception:
        return None
