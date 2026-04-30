from datetime import datetime, timedelta
from smtplib import SMTPDataError
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from users.models.user import User
from users.views.admin_actions import do_user_admin_actions


class UserAdminActionTests(TestCase):
    @patch("users.models.user.save_user_to_integration")
    def test_unmoderate_does_not_fail_when_email_is_rejected(self, _):
        now = datetime.utcnow()
        moderator = User.objects.create(
            email="moderator@example.com",
            full_name="Moderator",
            membership_started_at=now - timedelta(days=1),
            membership_expires_at=now + timedelta(days=1),
            moderation_status=User.MODERATION_STATUS_APPROVED,
            roles=[User.ROLE_MODERATOR],
        )
        user = User.objects.create(
            email="rejected-recipient@example.com",
            full_name="Rejected Recipient",
            membership_started_at=now - timedelta(days=1),
            membership_expires_at=now + timedelta(days=1),
            moderation_status=User.MODERATION_STATUS_APPROVED,
        )
        data = {
            "role": None,
            "role_action": None,
            "remove_hat": False,
            "add_hat": False,
            "new_achievement": None,
            "is_banned": False,
            "is_rejected": True,
            "delete_account": False,
            "ping": None,
            "add_membership_days": None,
        }

        with patch(
            "users.views.admin_actions.send_unmoderated_email",
            side_effect=SMTPDataError(553, b"No valid recipients"),
        ), patch("users.views.admin_actions.notify_admin_user_unmoderate") as notify_admin:
            do_user_admin_actions(SimpleNamespace(me=moderator), user, data)

        user.refresh_from_db()
        self.assertEqual(user.moderation_status, User.MODERATION_STATUS_REJECTED)
        notify_admin.assert_called_once_with(user)
