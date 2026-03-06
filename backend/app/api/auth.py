"""
JWT Authentication & RBAC Module

Provides user registration, login, token refresh, and role-based access control.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from passlib.context import CryptContext

from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, UserRole
from app.utils.security import security_manager, get_current_user

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory user store (swap for MongoDB in production)
_users_db: Dict[str, Dict[str, Any]] = {}

# Default admin user (created on first launch)
DEFAULT_ADMIN = {
    "id": "admin-001",
    "username": "admin",
    "email": "admin@nids.local",
    "password_hash": pwd_context.hash("admin123"),
    "role": UserRole.ADMIN.value,
    "is_active": True,
    "created_at": datetime.now().isoformat(),
    "last_login": None,
}
_users_db["admin"] = DEFAULT_ADMIN


def register_user(data: UserCreate) -> Optional[UserResponse]:
    """Register a new user."""
    if data.username in _users_db:
        return None  # username taken

    user = {
        "id": f"user-{len(_users_db) + 1:04d}",
        "username": data.username,
        "email": data.email,
        "password_hash": pwd_context.hash(data.password),
        "role": data.role.value,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
    }
    _users_db[data.username] = user
    logger.info(f"User registered: {data.username} ({data.role.value})")
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


def authenticate(data: UserLogin) -> Optional[TokenResponse]:
    """Authenticate user and return tokens."""
    user = _users_db.get(data.username)
    if not user:
        return None
    if not pwd_context.verify(data.password, user["password_hash"]):
        return None

    user["last_login"] = datetime.now().isoformat()

    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
    }

    access = security_manager.create_access_token(payload)
    refresh = security_manager.create_refresh_token(payload)

    from app.utils.config import settings
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


def refresh_token(token: str) -> Optional[TokenResponse]:
    """Refresh access token using refresh token."""
    try:
        payload = security_manager.verify_token(token)
        if payload.get("type") != "refresh":
            return None

        new_payload = {
            "sub": payload["sub"],
            "username": payload["username"],
            "role": payload["role"],
        }

        access = security_manager.create_access_token(new_payload)
        refresh = security_manager.create_refresh_token(new_payload)

        from app.utils.config import settings
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        )
    except Exception:
        return None


def get_user(username: str) -> Optional[UserResponse]:
    user = _users_db.get(username)
    if not user:
        return None
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
        last_login=user.get("last_login"),
    )

# ============================================================
# API Endpoints
# ============================================================

@router.post("/register", response_model=UserResponse)
async def api_register(data: UserCreate):
    user = register_user(data)
    if not user:
        raise HTTPException(status_code=400, detail="Username already exists")
    return user

@router.post("/login", response_model=TokenResponse)
async def api_login(data: UserLogin):
    tokens = authenticate(data)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return tokens

@router.get("/me", response_model=UserResponse)
async def api_me(current_user: dict = Depends(get_current_user)):
    user = get_user(current_user["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
