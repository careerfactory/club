import functools
from typing import Optional

from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749 import MissingAuthorizationError
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.views.decorators.csrf import csrf_exempt

from authn.models.openid import OAuth2App
from authn.providers.openid import oauth2_token_validator
from club.exceptions import ApiException, ClubException, ApiAuthRequired
from users.models.user import User


def api(require_auth=True, scopes=None):
    def decorator(view):
        @csrf_exempt
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            # check auth if needed
            authenticated_with_api_token = False
            if require_auth:
                # requests on behalf of apps (user == owner, for a simplicity)
                service_token = request.headers.get("X-Service-Token")
                if service_token:
                    request.me = user_by_service_token(service_token)
                    authenticated_with_api_token = True

                # oauth requests for API
                oauth_access_token = request.headers.get("Authorization")
                if oauth_access_token:
                    try:
                        token = oauth2_token_validator.acquire_token(request, scopes)
                    except MissingAuthorizationError as ex:
                        raise ApiAuthRequired(title="Missing OAuth token", message=str(ex))
                    except OAuth2Error as ex:
                        raise ApiAuthRequired(title="OAuth token error", message=str(ex))

                    request.me = token.user
                    authenticated_with_api_token = True

                # this user can also come from other types of auth (e.g. cookies)
                if not request.me:
                    raise ApiAuthRequired()

                # CSRF protection for cookie-based browser auth.
                if is_unsafe_method(request) and not authenticated_with_api_token:
                    enforce_csrf(request)

            # execute view and catch exceptions
            status_code = 200
            try:
                results = view(request, *args, **kwargs)
            except ApiException:
                raise  # simply re-raise
            except ClubException as ex:
                # wrap and re-raise
                raise ApiException(
                    code=ex.code,
                    title=ex.title,
                    message=ex.message,
                    data=ex.data,
                )
            except Exception as ex:
                raise ApiException(
                    code=ex.__class__.__name__,
                    title=str(ex),
                )

            # return results in expected format
            if is_ajax(request):  # legacy, change to Content-Type check
                return JsonResponse(data=results, status=status_code, json_dumps_params=dict(ensure_ascii=False))
            elif isinstance(results, dict):
                return JsonResponse(data=results, status=status_code, json_dumps_params=dict(ensure_ascii=False))
            elif isinstance(results, str):
                return HttpResponse(results, content_type="text/plain; charset=utf-8")
            else:
                return results

        return wrapper
    return decorator


def is_ajax(request):
    return bool(request.GET.get("is_ajax"))


def is_unsafe_method(request) -> bool:
    return request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}


def enforce_csrf(request):
    rejection = CsrfViewMiddleware(lambda _request: HttpResponse()).process_view(request, None, (), {})
    if rejection is not None:
        raise ApiAuthRequired(title="CSRF validation failed", message="Missing or invalid CSRF token")


def user_by_service_token(service_token) -> Optional[User]:
    app = OAuth2App.objects\
        .filter(service_token=service_token)\
        .select_related("owner")\
        .first()

    if not app:
        return None  # no such app

    return app.owner
