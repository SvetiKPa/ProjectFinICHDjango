from datetime import datetime

from django.utils.timezone import make_aware
from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookies(response, user) -> None:
    refresh_token = RefreshToken.for_user(user)
    access_token = refresh_token.access_token

    access_exp = make_aware(
        datetime.fromtimestamp(access_token['exp'])
    )
    refresh_exp = make_aware(
        datetime.fromtimestamp(refresh_token['exp'])
    )

    response.set_cookie(
        key='access_token',
        value=str(access_token),
        httponly=True,
        secure=True,
        samesite='Strict',
        expires=access_exp
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh_token),
        httponly=True,
        secure=True,
        samesite='Strict',
        expires=refresh_exp
    )
