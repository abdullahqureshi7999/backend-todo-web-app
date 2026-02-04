"""JWT verification using JWKS from Better Auth"""
import jwt
from jwt import PyJWKClient
from typing import Dict
from src.config import settings
import logging


logger = logging.getLogger(__name__)


# JWKS client for Better Auth
# Better Auth is mounted at /api/auth, JWKS endpoint is at /api/auth/.well-known/jwks.json
jwks_url = f"{settings.better_auth_url}/api/auth/.well-known/jwks.json"
jwks_client = PyJWKClient(jwks_url)


def verify_jwt(token: str) -> Dict[str, any]:
    """
    Verify JWT token using JWKS from Better Auth

    Args:
        token: JWT token string

    Returns:
        Decoded token payload containing user information

    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    try:
        # Get signing key from JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode and verify token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
        )

        logger.debug(f"JWT verified successfully for user: {payload.get('sub')}")
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error verifying JWT: {e}", exc_info=True)
        logger.error(f"JWKS URL: {jwks_url}")
        logger.error(f"Better Auth URL: {settings.better_auth_url}")
        raise jwt.InvalidTokenError(f"Token verification failed: {e}")


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from JWT token

    Args:
        token: JWT token string

    Returns:
        User ID from token subject claim

    Raises:
        jwt.InvalidTokenError: If token is invalid or missing subject
    """
    payload = verify_jwt(token)

    user_id = payload.get("sub")
    if not user_id:
        raise jwt.InvalidTokenError("Token missing 'sub' claim")

    return user_id
