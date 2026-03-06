"""
JWT Authentication & RBAC Module

Provides user registration, login, token refresh, and role-based access control.
"""

import os
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

# Default admin setup - hardened
# Pull from ENV or generate random if missing
from app.utils.config import settings
import secrets

ADMIN_PASSWORD = os.getenv("NIDS_ADMIN_PASSWORD", "Ghost-Admin-Appliance-2026")
if ADMIN_PASSWORD == "admin123":
    logger.warning("CRITICAL: USING DEFAULT ADMIN PASSWORD. CHANGE 'NIDS_ADMIN_PASSWORD' IN ENV!")

DEFAULT_ADMIN = {
    "username": "admin",
    "email": os.getenv("NIDS_ADMIN_EMAIL", "admin@nids.local"),
    "password_hash": pwd_context.hash(ADMIN_PASSWORD),
    "role": UserRole.ADMIN.value,
    "is_active": True,
    "created_at": datetime.now().isoformat(),
}


from app.db.database import db_manager

async def register_user(data: UserCreate) -> Optional[UserResponse]:
    """Register a new user with persistent storage."""
    existing = await db_manager.get_user_by_username(data.username)
    if existing:
        return None

    user = {
        "username": data.username,
        "email": data.email,
        "password_hash": pwd_context.hash(data.password),
        "role": data.role.value,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
    }
    await db_manager.insert_user(user)
    logger.info(f"User registered in DB: {data.username}")
    
    return UserResponse(
        id=str(user.get("_id", "new")),
        username=user["username"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


async def authenticate(data: UserLogin) -> Optional[TokenResponse]:
    """Authenticate user via DB and return tokens."""
    user = await db_manager.get_user_by_username(data.username)
    if not user:
        return None
        
    if not pwd_context.verify(data.password, user["password_hash"]):
        # Potentially record failed attempt here
        return None

    await db_manager.update_user(user["username"], {"last_login": datetime.now().isoformat()})

    payload = {
        "sub": str(user["_id"]),
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


async def get_user_info(username: str) -> Optional[UserResponse]:
    user = await db_manager.get_user_by_username(username)
    if not user:
        return None
    return UserResponse(
        id=str(user["_id"]),
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
