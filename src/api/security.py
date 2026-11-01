import os
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str


def decode_access_token(token: str) -> Principal:
    secret = os.environ.get("JWT_SECRET_KEY")

    if not secret or len(secret) < 32:
        raise RuntimeError("JWT secret is not configured securely.")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=os.environ["JWT_ISSUER"],
            audience=os.environ["JWT_AUDIENCE"],
            options={
                "require": ["exp", "iat", "sub", "iss", "aud"]
            },
        )

        user_id = payload.get("sub")

        if not isinstance(user_id, str) or not user_id.strip():
            raise jwt.InvalidTokenError("Invalid subject.")

        return Principal(user_id=user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Principal:

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decode_access_token(credentials.credentials)