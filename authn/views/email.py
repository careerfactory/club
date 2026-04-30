from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django_q.tasks import async_task

from authn.helpers import set_session_cookie
from authn.models.session import Session, Code
from club import features
from notifications.email.users import send_auth_email
from notifications.telegram.users import notify_user_auth
from users.models.user import User

log = logging.getLogger(__name__)


def sign_in_user(response, user):
    changed = False

    if user.moderation_status == User.MODERATION_STATUS_INTRO and not user.is_active_membership:
        user.membership_expires_at = datetime.utcnow() + timedelta(days=30)
        changed = True

    if not user.is_email_verified:
        user.is_email_verified = True
        changed = True

    if user.deleted_at:
        user.deleted_at = None
        changed = True

    if changed:
        user.save()

    session = Session.create_for_user(user)
    return set_session_cookie(response, user, session)


def get_legacy_secret_login(request):
    email_or_login = request.POST.get("email_or_login") or request.GET.get("email_or_login")
    if email_or_login:
        email_or_login = email_or_login.strip()
        if "|-" in email_or_login:
            return email_or_login.rsplit("|-", 1)

    email = request.GET.get("email")
    secret_hash = request.GET.get("secret_hash") or request.GET.get("secret")
    if email and secret_hash:
        return email, secret_hash

    return None, None


def safe_redirect_target(request, target):
    if not target:
        return None

    allowed_hosts = {request.get_host(), *settings.ALLOWED_HOSTS}
    if url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts=allowed_hosts,
        require_https=not settings.DEBUG,
    ):
        return target

    log.warning("Blocked unsafe redirect target: %s", target)
    return None


def email_login(request):
    legacy_email, legacy_secret_hash = get_legacy_secret_login(request)
    if legacy_email and legacy_secret_hash:
        email = legacy_email.lower().strip()
        secret_hash = legacy_secret_hash.strip()

        user = User.objects.filter(email=email, secret_hash=secret_hash).first()
        if not user:
            return render(request, "error.html", {
                "title": "Такого юзера нет 🤔",
                "message": "Пользователь с такой почтой не найден в списке членов Клуба. "
                           "Попробуйте другую почту или никнейм. "
                           "Если совсем ничего не выйдет, напишите нам, попробуем помочь.",
            }, status=404)

        response = redirect(reverse("profile", args=[user.slug]))
        return sign_in_user(response, user)

    if request.method != "POST":
        return redirect("login")

    goto = request.POST.get("goto")
    email_or_login = request.POST.get("email_or_login")
    if not email_or_login:
        return redirect("login")

    email_or_login = email_or_login.strip()

    if features.FREE_MEMBERSHIP:
        # email login or sign up
        now = datetime.utcnow()

        try:
            log.info("Add new user %s", email_or_login)

            user, created = User.objects.get_or_create(
                email=email_or_login.lower(),
                defaults=dict(
                    membership_platform_type=User.MEMBERSHIP_PLATFORM_DIRECT,
                    full_name=email_or_login[:email_or_login.find("@")],
                    membership_started_at=now,
                    membership_expires_at=now + timedelta(days=365),
                    created_at=now,
                    updated_at=now,
                    moderation_status=User.MODERATION_STATUS_INTRO,
                ),
            )

        except IntegrityError:
            return render(request, "error.html", {
                "title": "Что-то пошло не так 🤔",
                "message": "Напишите нам, и мы всё починим. Или попробуйте ещё раз.",
            }, status=404)
    else:
        # email/nickname login
        user = User.objects.filter(Q(email=email_or_login.lower()) | Q(slug=email_or_login)).first()
        if not user:
            return render(request, "error.html", {
                "title": "Такого юзера нет 🤔",
                "message": "Пользователь с такой почтой не найден в списке членов Клуба. "
                           "Попробуйте другую почту или никнейм. "
                           "Если совсем ничего не выйдет, напишите нам, попробуем помочь.",
            }, status=404)

    code = Code.create_for_user(user=user, recipient=user.email, length=settings.AUTH_CODE_LENGTH)
    async_task(send_auth_email, user, code)
    async_task(notify_user_auth, user, code)

    return render(request, "auth/email.html", {
        "email": user.email,
        "goto": goto,
        "restore": user.deleted_at is not None,
    })


def email_login_code(request):
    email = request.GET.get("email")
    code = request.GET.get("code")
    if not email or not code:
        return redirect("login")

    goto = request.GET.get("goto")
    email = email.lower().strip()
    code = code.lower().strip()

    user = Code.check_code(recipient=email, code=code)

    redirect_to = safe_redirect_target(request, goto) or reverse("profile", args=[user.slug])
    response = redirect(redirect_to)
    return sign_in_user(response, user)
