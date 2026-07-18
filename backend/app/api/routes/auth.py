"""
ARTHA Auth Routes
==================
JWT-based authentication with bcrypt password hashing.
Uses python-jose for JWT token generation and verification.

Endpoints:
- POST /auth/register — Create a new user account
- POST /auth/login    — Authenticate and receive JWT token
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.db.database import get_db
from app.db.models import User
from app.models.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT token management
# ---------------------------------------------------------------------------
security = HTTPBearer()

def create_access_token(user_id: UUID, email: str) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )


# ---------------------------------------------------------------------------
# Current user dependency
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the current user
    from the JWT token in the Authorization header.
    """
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # Get the generated ID

    # Generate token
    token = create_access_token(user.id, user.email)
    logger.info(f"New user registered: {user.email}")

    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive a JWT token."""
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(user.id, user.email)
    logger.info(f"User logged in: {user.email}")

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile and simulate 24-hour approval if pending."""
    if current_user.status == "pending_approval" and current_user.verification_requested_at:
        # Simulate 24-hour approval automatically
        time_elapsed = datetime.now(timezone.utc) - current_user.verification_requested_at
        if time_elapsed > timedelta(hours=24):
            current_user.status = "approved"
            db.add(current_user)
            await db.commit()
            await db.refresh(current_user)
            logger.info(f"User {current_user.email} automatically approved after 24 hours.")
            
    return current_user

@router.post("/verification", response_model=UserResponse)
async def submit_verification(
    institution: str = Form(...),
    role: str = Form(...),
    id_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit verification details and ID document."""
    if current_user.status != "unverified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification already submitted or approved."
        )

    # Ensure upload directory exists
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "ids")
    os.makedirs(upload_dir, exist_ok=True)

    # Save the file
    file_extension = os.path.splitext(id_file.filename)[1] if id_file.filename else ".pdf"
    file_name = f"{current_user.id}_id{file_extension}"
    file_path = os.path.join(upload_dir, file_name)

    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await id_file.read()
            await out_file.write(content)
    except Exception as e:
        logger.error(f"Failed to save ID document: {e}")
        raise HTTPException(status_code=500, detail="Could not save file")

    # Update user record
    current_user.institution = institution
    current_user.role = role
    current_user.id_document_path = file_path
    current_user.status = "pending_approval"
    current_user.verification_requested_at = datetime.now(timezone.utc)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User {current_user.email} submitted verification request.")
    return current_user

@router.post("/admin", response_model=TokenResponse)
async def admin_login(db: AsyncSession = Depends(get_db)):
    """Background login for the admin backdoor page."""
    admin_email = "jiluadmin@gmail.com"
    admin_password = "jilujose"

    # Check if admin user exists
    result = await db.execute(
        select(User).where(User.email == admin_email)
    )
    user = result.scalar_one_or_none()

    # If not, create them
    if not user:
        user = User(
            email=admin_email,
            hashed_password=hash_password(admin_password),
            status="approved"
        )
        db.add(user)
        await db.flush()
        logger.info(f"Created hardcoded admin user: {admin_email}")

    # Generate token
    token = create_access_token(user.id, user.email)
    logger.info(f"Admin background login: {user.email}")

    return TokenResponse(access_token=token)

@router.get("/admin/requests", response_model=list[UserResponse])
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users pending approval (Admin only)."""
    if current_user.email != "jiluadmin@gmail.com":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    result = await db.execute(
        select(User).where(User.status == "pending_approval").order_by(User.verification_requested_at.desc())
    )
    return result.scalars().all()

@router.post("/admin/approve/{user_id}", response_model=UserResponse)
async def approve_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending verification request (Admin only)."""
    if current_user.email != "jiluadmin@gmail.com":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.status != "pending_approval":
        raise HTTPException(status_code=400, detail="User is not pending approval")
        
    user.status = "approved"
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Admin approved user: {user.email}")
    return user
