import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import AuthUser, Organization, OnboardingState, AuditLog, EmailVerificationToken
from app.services.security import hash_password

router = APIRouter(prefix="/registration", tags=["public registration"])


class RegistrationBody(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+
    password: str = Field(min_length=12, max_length=256)
    country: str = Field(min_length=2, max_length=100)
    industry: str = Field(min_length=2, max_length=100)


class VerifyBody(BaseModel):
    token: str = Field(min_length=32, max_length=256)


def _send_verification_email(recipient: str, token: str):
    required = [settings.SMTP_HOST, settings.SMTP_FROM_EMAIL, settings.PUBLIC_APP_URL]
    if not all(required):
        raise HTTPException(503, "Company registration is temporarily unavailable: email verification is not configured.")
    link = settings.PUBLIC_APP_URL.rstrip("/") + "/?verify=" + token
    message = EmailMessage()
    message["Subject"] = "Verify your Cyber DNA company account"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(
        "Welcome to Cyber DNA. Verify your email address using this link:\n\n"
        + link + "\n\nThis link expires in 30 minutes. If you did not request this account, ignore this email."
    )
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
            smtp.send_message(message)
    except Exception:
        raise HTTPException(503, "We could not send the verification email. Please try again later.")


@router.post("", status_code=202)
def register_company(body: RegistrationBody, db: Session = Depends(get_db)):
    email = str(body.email).strip().lower()
    if db.query(AuthUser).filter((AuthUser.email == email) | (AuthUser.username == email)).first():
        raise HTTPException(409, "An account with this email already exists.")
    if not all([settings.SMTP_HOST, settings.SMTP_FROM_EMAIL, settings.PUBLIC_APP_URL]):
        raise HTTPException(503, "Company registration is not available until email verification is configured.")
    org = Organization(
        name=body.company_name.strip(),
        country=body.country.strip(),
        industry=body.industry.strip(),
        contact_email=email,
        status="pending_email_verification",
    )
    user = AuthUser(
        username=email,
        email=email,
        password_hash=hash_password(body.password),
        role="org_admin",
        organization=org,
        is_active=False,
        must_change_password=False,
    )
    db.add(org)
    db.add(user)
    db.flush()
    db.add(OnboardingState(organization_id=org.id))
    raw_token = secrets.token_urlsafe(40)
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    db.add(EmailVerificationToken(
        user_id=user.id,
        token_hash=digest,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    ))
    db.add(AuditLog(
        actor_user_id=user.id,
        organization_id=org.id,
        action="public_company_registration_requested",
        details={"email": email},
    ))
    db.commit()
    try:
        _send_verification_email(email, raw_token)
    except HTTPException:
        db.delete(user)
        db.delete(org)
        db.commit()
        raise
    return {"accepted": True, "message": "Check your email for a verification link."}


@router.post("/verify")
def verify_company_email(body: VerifyBody, db: Session = Depends(get_db)):
    digest = hashlib.sha256(body.token.encode()).hexdigest()
    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == digest,
        EmailVerificationToken.used_at.is_(None),
    ).first()
    now = datetime.now(timezone.utc)
    if not record:
        raise HTTPException(400, "This verification link is invalid or has already been used.")
    expiry = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if expiry <= now:
        raise HTTPException(400, "This verification link has expired. Please contact support.")
    user = db.query(AuthUser).filter(AuthUser.id == record.user_id).first()
    if not user:
        raise HTTPException(400, "This verification link is no longer valid.")
    record.used_at = now
    user.is_active = True
    if user.organization:
        user.organization.status = "onboarding"
    db.add(AuditLog(
        actor_user_id=user.id,
        organization_id=user.organization_id,
        action="company_email_verified",
        details={},
    ))
    db.commit()
    return {"verified": True, "message": "Email verified. You can now sign in and complete company onboarding."}
)
    password: str = Field(min_length=12, max_length=256)
    country: str = Field(min_length=2, max_length=100)
    industry: str = Field(min_length=2, max_length=100)


class VerifyBody(BaseModel):
    token: str = Field(min_length=32, max_length=256)


def _send_verification_email(recipient: str, token: str):
    required = [settings.SMTP_HOST, settings.SMTP_FROM_EMAIL, settings.PUBLIC_APP_URL]
    if not all(required):
        raise HTTPException(503, "Company registration is temporarily unavailable: email verification is not configured.")
    link = settings.PUBLIC_APP_URL.rstrip("/") + "/?verify=" + token
    message = EmailMessage()
    message["Subject"] = "Verify your Cyber DNA company account"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(
        "Welcome to Cyber DNA. Verify your email address using this link:\n\n"
        + link + "\n\nThis link expires in 30 minutes. If you did not request this account, ignore this email."
    )
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
            smtp.send_message(message)
    except Exception:
        raise HTTPException(503, "We could not send the verification email. Please try again later.")


@router.post("", status_code=202)
def register_company(body: RegistrationBody, db: Session = Depends(get_db)):
    email = str(body.email).strip().lower()
    if db.query(AuthUser).filter((AuthUser.email == email) | (AuthUser.username == email)).first():
        raise HTTPException(409, "An account with this email already exists.")
    if not all([settings.SMTP_HOST, settings.SMTP_FROM_EMAIL, settings.PUBLIC_APP_URL]):
        raise HTTPException(503, "Company registration is not available until email verification is configured.")
    org = Organization(
        name=body.company_name.strip(),
        country=body.country.strip(),
        industry=body.industry.strip(),
        contact_email=email,
        status="pending_email_verification",
    )
    user = AuthUser(
        username=email,
        email=email,
        password_hash=hash_password(body.password),
        role="org_admin",
        organization=org,
        is_active=False,
        must_change_password=False,
    )
    db.add(org)
    db.add(user)
    db.flush()
    db.add(OnboardingState(organization_id=org.id))
    raw_token = secrets.token_urlsafe(40)
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    db.add(EmailVerificationToken(
        user_id=user.id,
        token_hash=digest,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    ))
    db.add(AuditLog(
        actor_user_id=user.id,
        organization_id=org.id,
        action="public_company_registration_requested",
        details={"email": email},
    ))
    db.commit()
    try:
        _send_verification_email(email, raw_token)
    except HTTPException:
        db.delete(user)
        db.delete(org)
        db.commit()
        raise
    return {"accepted": True, "message": "Check your email for a verification link."}


@router.post("/verify")
def verify_company_email(body: VerifyBody, db: Session = Depends(get_db)):
    digest = hashlib.sha256(body.token.encode()).hexdigest()
    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == digest,
        EmailVerificationToken.used_at.is_(None),
    ).first()
    now = datetime.now(timezone.utc)
    if not record:
        raise HTTPException(400, "This verification link is invalid or has already been used.")
    expiry = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
    if expiry <= now:
        raise HTTPException(400, "This verification link has expired. Please contact support.")
    user = db.query(AuthUser).filter(AuthUser.id == record.user_id).first()
    if not user:
        raise HTTPException(400, "This verification link is no longer valid.")
    record.used_at = now
    user.is_active = True
    if user.organization:
        user.organization.status = "onboarding"
    db.add(AuditLog(
        actor_user_id=user.id,
        organization_id=user.organization_id,
        action="company_email_verified",
        details={},
    ))
    db.commit()
    return {"verified": True, "message": "Email verified. You can now sign in and complete company onboarding."}
