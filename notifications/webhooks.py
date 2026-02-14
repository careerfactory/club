import hmac
import json

from django.conf import settings
from django.http import HttpResponse

from notifications.models import WebhookEvent


def webhook_event(request, event_type):
    secret = request.headers.get("X-Webhook-Secret")
    if not has_valid_webhook_secret(secret):
        return HttpResponse("Bad secret", status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {"body": str(request.body)}

    handler = WEBHOOK_HANDLERS.get(event_type) or WEBHOOK_HANDLERS["default"]
    handler(
        event_type=event_type,
        data=data,
    )
    return HttpResponse("OK")


def default_webhook_handler(event_type, data):
    return WebhookEvent.register_event(
        type=event_type,
        recipient=None,
        data=data
    )


WEBHOOK_HANDLERS = {
    WebhookEvent.TYPE_EMAIL_BOUNCE: default_webhook_handler,
    WebhookEvent.TYPE_EMAIL_COMPLAINT: default_webhook_handler,
    "default": default_webhook_handler,
}


def has_valid_webhook_secret(secret: str) -> bool:
    if not secret:
        return False

    for allowed_secret in settings.WEBHOOK_SECRETS:
        if not allowed_secret:
            continue
        if hmac.compare_digest(secret, allowed_secret):
            return True

    return False
