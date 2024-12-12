import logging

import requests

from django.conf import settings

log = logging.getLogger(__name__)

HEADERS = {"Authorization": "Bearer " + settings.INTEGRATION_TOKEN}


def save_user_to_integration(user):
    data = {
        "id": str(user.id),
        "name": user.full_name,
        "email": user.email,
        "telegram_id": user.telegram_id,
        "is_active_member": user.is_active_member,
    }
    try:
        requests.post(settings.INTEGRATION_USER_URL, json=data, headers=HEADERS)
        log.info("User slug=%s update sent to integration", user.slug)
    except Exception as e:
        log.warning("Saving to integration failed", exc_info=e)
