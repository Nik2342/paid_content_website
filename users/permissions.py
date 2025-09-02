import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login

User = get_user_model()


def check_jwt_authentication(request):

    if hasattr(request, "user") and request.user.is_authenticated:
        return True

    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                login(request, user)
                return True
        except (jwt.InvalidTokenError, User.DoesNotExist):
            pass

    token_cookie = request.COOKIES.get("access_token")
    if token_cookie:
        try:
            payload = jwt.decode(
                token_cookie, settings.SECRET_KEY, algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                login(request, user)
                return True
        except (jwt.InvalidTokenError, User.DoesNotExist):
            pass

    return False


class IsJWTAuthenticated:

    def has_permission(self, request, view):
        return check_jwt_authentication(request)


class HasPaidSubscription:

    def has_permission(self, request, view):
        if not check_jwt_authentication(request):
            return False
        return request.user.has_paid_subscription
