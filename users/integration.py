import logging
import os
import sys

import django
import requests

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "club.settings")
    django.setup()

from django.conf import settings

log = logging.getLogger(__name__)


def save_user_to_integration(user):
    data = {
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "telegram_id": user.telegram_id,
        "is_active_member": user.is_active_member,
    }
    headers = {"Authorization": "Bearer " + settings.INTEGRATION_TOKEN}
    try:
        requests.post(settings.INTEGRATION_USER_URL, json=data, headers=headers)
        log.info("User slug=%s update sent to integration", user.slug)
    except Exception as e:
        log.warning("Saving to integration failed", exc_info=e)


def import_all_users():
    from .models.user import User

    users = User.objects.all()
    for user in users:
        save_user_to_integration(user)


if __name__ == "__main__":
    import_all_users()
