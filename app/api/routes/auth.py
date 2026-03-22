import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext
from authlib.integrations.starlette_client import OAuth, OAuthError

from app.models.schemas import RegisterRequest, LoginRequest, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.models.db import User, PasswordResetToken
from app.core.config import settings
from app.api.deps import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google OAuth client
oauth = OAuth()
if settings.google_client_id:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def send_reset_email(to_email: str, name: str, reset_url: str):
    import aiosmtplib
    from email.mime.text import MIMEText
    msg = MIMEText(
        f"Hi {name},\n\nClick the link below to reset your password (valid for 1 hour):\n\n{reset_url}\n\nIf you didn't request this, ignore this email.",
        "plain",
    )
    msg["Subject"] = "Reset your LegalDoc AI password"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    await aiosmtplib.send(msg, hostname=settings.smtp_host, port=settings.smtp_port,
                          username=settings.smtp_user, password=settings.smtp_password, start_tls=True)


# ── Register ──────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(email=body.email, full_name=body.full_name, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(access_token=create_token(user.id), user_id=user.id, full_name=user.full_name, email=user.email)


# ── Login ─────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return TokenResponse(access_token=create_token(user.id), user_id=user.id, full_name=user.full_name, email=user.email)


# ── Google OAuth ──────────────────────────────────────────
@router.get("/google/login")
async def google_login(request: Request):
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured.")
    redirect_uri = str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(f"{settings.frontend_url}/login?error=google_failed")

    user_info = token.get("userinfo")
    if not user_info:
        return RedirectResponse(f"{settings.frontend_url}/login?error=google_failed")

    result = await db.execute(select(User).where(User.email == user_info["email"]))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=user_info["email"], full_name=user_info.get("name", ""), hashed_password="")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    jwt_token = create_token(user.id)
    return RedirectResponse(
        f"{settings.frontend_url}/auth/callback?token={jwt_token}&user_id={user.id}&name={user.full_name}&email={user.email}"
    )


# ── Forgot Password ───────────────────────────────────────
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Always return success to avoid revealing if email exists
    if not user:
        return {"message": "If this email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at))
    await db.commit()

    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    if settings.smtp_host:
        try:
            await send_reset_email(user.email, user.full_name, reset_url)
            return {"message": "Reset link sent to your email."}
        except Exception:
            pass

    # Dev mode — return the URL directly so it works without SMTP
    return {"message": "Reset link generated.", "reset_url": reset_url}


# ── Reset Password ────────────────────────────────────────
@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    reset = result.scalar_one_or_none()
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    result = await db.execute(select(User).where(User.id == reset.user_id))
    user = result.scalar_one_or_none()
    user.hashed_password = hash_password(body.new_password)
    reset.used = True
    await db.commit()

    return {"message": "Password reset successfully. You can now log in."}
