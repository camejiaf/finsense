"""
Authentication and authorization module for FinSense
Professional JWT-based authentication system
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os

# Configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()

# In-memory user store (for demo - use database in production)
fake_users_db = {
    "demo@finsense.com": {
        "email": "demo@finsense.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "full_name": "Demo User",
        "disabled": False,
        "role": "user"
    },
    "admin@finsense.com": {
        "email": "admin@finsense.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # admin
        "full_name": "Admin User",
        "disabled": False,
        "role": "admin"
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class User(BaseModel):
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: Optional[str] = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def get_user(db: dict, email: str) -> Optional[UserInDB]:
    """Get user from database"""
    if email in db:
        user_dict = db[email]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db: dict, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = get_user(fake_db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials,
                             SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user(fake_users_db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Rate limiting with user context


def check_user_rate_limit(user_email: str, request_counts: Dict[str, list]) -> bool:
    """Check rate limit for authenticated user"""
    current_time = datetime.utcnow().timestamp()
    RATE_LIMIT_WINDOW = 60
    RATE_LIMIT_MAX_REQUESTS = 100  # Higher limit for authenticated users

    # Clean old requests
    request_counts[user_email] = [
        req_time for req_time in request_counts.get(user_email, [])
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check limit
    if len(request_counts.get(user_email, [])) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Add current request
    if user_email not in request_counts:
        request_counts[user_email] = []
    request_counts[user_email].append(current_time)
    return True

