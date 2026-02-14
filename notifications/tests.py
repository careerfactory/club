import json

from django.test import TestCase
from django.urls import reverse

from notifications.models import WebhookEvent


class NotificationWebhookSecurityTests(TestCase):
    def test_query_secret_is_rejected(self):
        with self.settings(WEBHOOK_SECRETS={"test-secret"}):
            response = self.client.post(
                reverse("webhook_event", args=[WebhookEvent.TYPE_EMAIL_BOUNCE]) + "?secret=test-secret",
                data=json.dumps({"email": "user@example.com"}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 403)

    def test_header_secret_is_accepted(self):
        with self.settings(WEBHOOK_SECRETS={"test-secret"}):
            response = self.client.post(
                reverse("webhook_event", args=[WebhookEvent.TYPE_EMAIL_BOUNCE]),
                data=json.dumps({"email": "user@example.com"}),
                content_type="application/json",
                HTTP_X_WEBHOOK_SECRET="test-secret",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        event = WebhookEvent.objects.first()
        self.assertEqual(event.type, WebhookEvent.TYPE_EMAIL_BOUNCE)
