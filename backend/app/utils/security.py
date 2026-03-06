"""
Security Utilities — JWT, API key verification, middleware, input validation.
"""

import os
import jwt
import hashlib
import secrets
import ipaddress
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger("nids.security")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

bearer_scheme = HTTPBearer(auto_error=False)


class SecurityManager:
    """Centralized security manager for auth, tokens, and audit."""

    def __init__(self):
        from app.utils.config import settings
        self.settings = settings
        self.failed_attempts: Dict[str, int] = {}
        self.blocked_ips: set = set()

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.JWT_EXPIRATION_HOURS
        )
        payload["type"] = "access"
        return jwt.encode(payload, self.settings.JWT_SECRET, algorithm=self.settings.JWT_ALGORITHM)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(timezone.utc) + timedelta(
            days=self.settings.JWT_REFRESH_EXPIRATION_DAYS
        )
        payload["type"] = "refresh"
        return jwt.encode(payload, self.settings.JWT_SECRET, algorithm=self.settings.JWT_ALGORITHM)

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token, self.settings.JWT_SECRET,
                algorithms=[self.settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
        except jwt.JWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    def verify_api_key(self, provided_key: str) -> bool:
        if not self.settings.API_KEY:
            return False
        return secrets.compare_digest(self.settings.API_KEY, provided_key)

    def record_failed_attempt(self, ip: str):
        self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
        if self.failed_attempts[ip] >= 5:
            # Persistent Block
            import asyncio
            from app.db.database import db_manager
            asyncio.create_task(db_manager.add_blocked_ip(ip, "Brute force detected"))
            logger.warning(f"IP {ip} blocked persistently after repeated auth failures")

    async def is_ip_blocked(self, ip: str) -> bool:
        from app.db.database import db_manager
        return await db_manager.is_ip_blocked(ip)

    def log_event(self, event_type: str, details: Dict[str, Any], client_ip: str = None):
        sanitized = {
            k: ("***" if any(s in k.lower() for s in ("password", "secret", "key", "token")) else v)
            for k, v in details.items()
        }
        logger.info(f"[{event_type}] ip={client_ip} {sanitized}")


security_manager = SecurityManager()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Verify API key passed as Bearer token."""
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing credentials")
    if not security_manager.verify_api_key(credentials.credentials):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    return credentials.credentials


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Extract user from JWT token."""
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing credentials")
    payload = security_manager.verify_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    return payload


def require_role(*roles: str):
    """Factory for role-based access control."""
    async def _dependency(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return _dependency


def get_client_ip(request: Request) -> str:
    """Extract real client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


class InputValidator:
    @staticmethod
    def validate_ip(ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_interface(name: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9\s\-_.]+$', name)) and len(name) <= 50

    @staticmethod
    def validate_port(port: int) -> bool:
        return isinstance(port, int) and 1 <= port <= 65535

    @staticmethod
    def sanitize(text: str, max_length: int = 255) -> str:
        return ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')[:max_length]


input_validator = InputValidator()


class SecurityMiddleware:
    """ASGI middleware that injects security headers."""

    SECURITY_HEADERS = {
        b"X-Content-Type-Options": b"nosniff",
        b"X-Frame-Options": b"DENY",
        b"X-XSS-Protection": b"1; mode=block",
        b"Strict-Transport-Security": b"max-age=31536000; includeSubDomains",
        b"Referrer-Policy": b"strict-origin-when-cross-origin",
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    for k, v in self.SECURITY_HEADERS.items():
                        headers.append((k, v))
                    message["headers"] = headers
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
