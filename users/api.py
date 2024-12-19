from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404

from authn.decorators.api import api
from club.exceptions import ApiAccessDenied
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
