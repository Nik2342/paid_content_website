import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if not hasattr(request, "user") or not request.user.is_authenticated:
                token = self.get_token_from_request(request)
                if token:
                    user = self.authenticate_with_token(token)
                    if user:
                        request.user = user
                        login(request, user)
                        logger.debug(f"User {user.id} authenticated via JWT middleware")

        except Exception as e:
            logger.error(f"JWT middleware error: {e}")

        return self.get_response(request)

    def get_token_from_request(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        return request.COOKIES.get("access_token")

    def authenticate_with_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if user_id:
                return User.objects.get(id=user_id)
        except jwt.ExpiredSignatureError:
            logger.debug("JWT token expired")
        except jwt.InvalidTokenError:
            logger.debug("Invalid JWT token")
        except User.DoesNotExist:
            logger.debug("User from JWT token does not exist")

        return None
