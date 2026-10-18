import os
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=8)
def _jwks_client(issuer: str) -> PyJWKClient:
    return PyJWKClient(f"{issuer}/.well-known/jwks.json")


def require_cognito_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wymagane jest zalogowanie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    region = os.getenv("COGNITO_REGION", "")
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID", "")
    client_id = os.getenv("COGNITO_USER_POOL_CLIENT_ID", "")
    if not region or not user_pool_id or not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Uwierzytelnianie Cognito nie jest skonfigurowane.",
        )

    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    try:
        signing_key = _jwks_client(issuer).get_signing_key_from_jwt(
            credentials.credentials
        )
    except jwt.PyJWKClientConnectionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nie można połączyć się z usługą weryfikacji tokenów.",
        ) from error
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token dostępu.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    try:
        claims: dict[str, Any] = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={
                "require": ["exp", "iss", "sub", "token_use", "client_id"],
                "verify_aud": False,
            },
        )
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token dostępu.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    if claims["token_use"] != "access" or claims["client_id"] != client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token nie jest przeznaczony dla tej aplikacji.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return claims
