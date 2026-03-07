import asyncio
import os
import sys
from datetime import datetime
from passlib.context import CryptContext

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import db_manager
from app.utils.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_admin():
    print("⏳ Connecting to MongoDB...")
    await db_manager.connect()
    
    if db_manager.db is None:
        print("❌ Failed to connect to database. Is MongoDB running?")
        return

    admin_username = "admin"
    # Use the same default as in auth.py if not in env
    admin_password = os.getenv("NIDS_ADMIN_PASSWORD", "Ghost-Admin-Appliance-2026")
    
    existing_user = await db_manager.get_user_by_username(admin_username)
    
    if existing_user:
        print(f"ℹ️ User '{admin_username}' already exists. Updating password...")
        await db_manager.update_user(admin_username, {
            "password_hash": pwd_context.hash(admin_password),
            "is_active": True,
            "role": "admin"
        })
    else:
        print(f"Creating default admin user: {admin_username}")
        user_data = {
            "username": admin_username,
            "email": os.getenv("NIDS_ADMIN_EMAIL", "admin@nids.local"),
            "password_hash": pwd_context.hash(admin_password),
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
        }
        await db_manager.insert_user(user_data)
    
    print(f"✅ Admin account ready!")
    print(f"   Username: {admin_username}")
    print(f"   Password: {admin_password}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_admin())
