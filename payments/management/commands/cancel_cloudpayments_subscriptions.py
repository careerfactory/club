import base64
import os
from typing import List

import requests
from django.core.management.base import BaseCommand, CommandError

# массово отключаем автосписания CloudPayments
CP_LIST_URL = "https://api.cloudpayments.ru/subscriptions/list"
CP_CANCEL_URL = "https://api.cloudpayments.ru/subscriptions/cancel"
HTTP_TIMEOUT = 15


def _auth_header(public_id: str, secret: str) -> str:
    token = base64.b64encode(f"{public_id}:{secret}".encode()).decode()
    return f"Basic {token}"


def _get_subscriptions(headers) -> List[dict]:
    resp = requests.post(CP_LIST_URL, headers=headers, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("Success"):
        raise CommandError(f"CloudPayments list error: {data}")
    return data.get("Model") or []


def _cancel_subscription(sub_id: str, headers) -> bool:
    resp = requests.post(
        CP_CANCEL_URL,
        headers=headers,
        data={"Id": sub_id},
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("Success"):
        raise CommandError(f"CloudPayments cancel error for {sub_id}: {data}")
    return True


class Command(BaseCommand):
    help = "Отменяет все активные подписки CloudPayments"

    def handle(self, *args, **options):
        public_id = os.getenv("CLOUDPAYMENTS_PUBLIC_ID")
        secret = os.getenv("CLOUDPAYMENTS_SECRET")
        if not public_id or not secret:
            raise CommandError("Нужны CLOUDPAYMENTS_PUBLIC_ID и CLOUDPAYMENTS_SECRET")

        headers = {"Authorization": _auth_header(public_id, secret)}

        subs = _get_subscriptions(headers)
        self.stdout.write(f"Найдено подписок: {len(subs)}")

        cancelled = 0
        for sub in subs:
            sub_id = sub.get("Id")
            if not sub_id:
                continue
            try:
                _cancel_subscription(sub_id, headers)
                cancelled += 1
                self.stdout.write(f"Отменена {sub_id}")
            except Exception as ex:
                self.stderr.write(f"Ошибка отмены {sub_id}: {ex}")

        self.stdout.write(f"Готово. Отменено: {cancelled}/{len(subs)}")
