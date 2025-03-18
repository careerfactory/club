import json
from datetime import datetime, timedelta, timezone

from django.http import HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404

from authn.decorators.api import api
from club.exceptions import ApiAccessDenied
from landing.views import add_days_to_user, create_user_member, expire_membership, post_user_invite
from users.models.user import User


@api(require_auth=True)
def api_profile(request, user_slug):
    if user_slug == "me":
        user_slug = request.me.slug

    user = get_object_or_404(User, slug=user_slug)

    if request.me.moderation_status != User.MODERATION_STATUS_APPROVED and request.me.id != user.id:
        raise ApiAccessDenied(title="Non-approved users can only access their own profiles")

    return JsonResponse({
        "user": user.to_dict()
    })


@api(require_auth=True)
def api_profile_by_telegram_id(request, telegram_id):
    user = get_object_or_404(User, telegram_id=telegram_id)

    return JsonResponse({
        "user": user.to_dict()
    })


@api(require_auth=True)
def api_profile_status(request):
    if not request.me.is_god:
        raise ApiAccessDenied(title="God only")

    email = request.GET.get("email", None)
    telegram_id = request.GET.get("telegram_id", None)
    if email is None and telegram_id is None:
        return HttpResponseBadRequest("Specify email and/or telegram_id")

    telegram_user = User.objects.filter(telegram_id=telegram_id)
    telegram_user = (
        telegram_user[0] if telegram_user and telegram_id is not None else None
    )
    email_user = User.objects.filter(email=email)
    email_user = email_user[0] if email_user and email is not None else None

    user_id = None
    active = None
    club_telegram_id = None
    club_email = None
    if telegram_user is not None:
        user_id = telegram_user.id
        active = telegram_user.is_active_member
        club_telegram_id = telegram_user.telegram_id
        club_email = telegram_user.email
    if email_user is not None:
        user_id = user_id or email_user.id
        active = active or email_user.is_active_member
        club_telegram_id = club_telegram_id or email_user.telegram_id
        club_email = club_email or email_user.email

    body = {
        "id": user_id,
        "is_active_member": active,
        "telegram_id": club_telegram_id,
        "email": club_email,
    }
    return JsonResponse(body)


@api(require_auth=True)
def invite_user(request):
    if not request.me.is_god:
        raise ApiAccessDenied(title="God only")

    if request.method != "POST":
        bodies = [
            {
                "days": 10,
                "email": "user@example.org",
            },
            {
                "days": 10,
                "telegram_id": "143106937",
            }
        ]
        return JsonResponse({"example_bodies": bodies})
    body = json.loads(request.body)
    days = body.get("days", None)
    if days is None:
        return HttpResponseBadRequest("Specify days")
    try:
        days = int(days)
        if days <= 0:
            return HttpResponseBadRequest("days must be greater than 0")
    except ValueError:
        return HttpResponseBadRequest("days must be int")
    email = body.get("email", None)
    telegram_id = body.get("telegram_id", None)
    if email is None and telegram_id is None:
        return HttpResponseBadRequest("Specify email or telegram_id")

    user = None
    if telegram_id is not None:
        user = User.objects.filter(telegram_id=telegram_id).first()
    if email is not None:
        user = User.objects.filter(email=email).first()

    if user is None:
        user = create_user_member(email, telegram_id, days)
        if telegram_id is not None:
            user.telegram_id = telegram_id
            user.save()
    else:
        add_days_to_user(user, days)
    post_user_invite(request, user)
    body = {
        "user_id": user.id,
        "membership_expires_at": user.membership_expires_at
    }
    return JsonResponse(body)


@api(require_auth=True)
def expire_user(request):
    if not request.me.is_god:
        raise ApiAccessDenied(title="God only")
    body = json.loads(request.body)
    email = body.get("email", None)
    telegram_id = body.get("telegram_id", None)
    if email is None and telegram_id is None:
        return HttpResponseBadRequest("Specify email or telegram_id")

    user = None
    if telegram_id is not None:
        user = User.objects.filter(telegram_id=telegram_id).first()
    if email is not None:
        user = User.objects.filter(email=email).first()
    if user is None:
        return HttpResponseNotFound("User not found")
    expire_membership(user)
    body = {
        "user_id": user.id,
        "membership_expires_at": user.membership_expires_at
    }
    return JsonResponse(body)
