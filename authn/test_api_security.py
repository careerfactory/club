from datetime import datetime, timedelta

import django
from django.test import TestCase, Client
from django.urls import reverse

from authn.models.openid import OAuth2App
from authn.models.session import Session
from tags.models import Tag
from users.models.user import User


django.setup()  # todo: how to run tests from PyCharm without this workaround?


class ApiServiceTokenTransportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(
            email="api-owner@xx.com",
            membership_started_at=datetime.now() - timedelta(days=5),
            membership_expires_at=datetime.now() + timedelta(days=5),
            slug="api_owner",
        )
        cls.oauth_app = OAuth2App.objects.create(name="security_app", owner=cls.owner)

    def test_query_service_token_rejected(self):
        response = self.client.get(
            reverse("api_profile", args=["me"]),
            data={"service_token": self.oauth_app.service_token},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("api-auth-required", response.content.decode(response.charset))

    def test_header_service_token_accepted(self):
        response = self.client.get(
            reverse("api_profile", args=["me"]),
            HTTP_X_SERVICE_TOKEN=self.oauth_app.service_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("api_owner", response.content.decode(response.charset))


class ApiCsrfForCookieAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            email="csrf-user@xx.com",
            membership_started_at=datetime.now() - timedelta(days=5),
            membership_expires_at=datetime.now() + timedelta(days=5),
            moderation_status=User.MODERATION_STATUS_APPROVED,
            slug="csrf_user",
        )
        cls.session = Session.create_for_user(cls.user)
        cls.tag = Tag.objects.create(code="security_tag", name="Security")

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.cookies["token"] = self.session.token

    def test_cookie_auth_post_without_csrf_rejected(self):
        response = self.client.post(reverse("toggle_tag", args=[self.tag.code]))

        self.assertEqual(response.status_code, 400)
        self.assertIn("CSRF validation failed", response.content.decode(response.charset))

    def test_cookie_auth_post_with_csrf_allowed(self):
        self.client.cookies["csrftoken"] = "known-token"

        response = self.client.post(
            reverse("toggle_tag", args=[self.tag.code]),
            HTTP_X_CSRFTOKEN="known-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('"status": "created"', response.content.decode(response.charset))
