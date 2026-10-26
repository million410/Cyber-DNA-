from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import AuthUser, AuditLog
from app.core.config import settings
from app.services.security import get_principal
from app.schemas import AnalystRequest, AnalystResponse
from app.services.analyst import ask, provider_status
from app.services.ml_detection import status as ml_status

router = APIRouter()


@router.get("/analyst/status")
def analyst_status():
    """Report local provider configuration without making a billable network request."""
    return {**provider_status(check_connectivity=False), "ml": ml_status()}


@router.post("/analyst/status/check")
def analyst_status_check():
    """Explicitly perform a small live Responses API request to verify credentials/model access."""
    return {**provider_status(check_connectivity=True), "ml": ml_status()}


@router.post("/analyst/ask", response_model=AnalystResponse)
def analyst_ask(
    request: AnalystRequest,
    user: AuthUser = Depends(get_principal),
    db: Session = Depends(get_db),
):
    # The publicly documented demo account shares a small, database-backed quota
    # across all visitors. Count attempts before the external model call so errors
    # do not become a way to bypass the limit.
    if user.role == "demo_viewer":
        limit = max(1, int(settings.CYBERDNA_DEMO_AI_REQUESTS_PER_HOUR))
        # Serialize quota checkouts for the shared account on PostgreSQL to reduce
        # over-limit races when several visitors submit at the same time.
        db.query(AuthUser).filter(AuthUser.id == user.id).with_for_update().one()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        used = db.query(AuditLog).filter(
            AuditLog.actor_user_id == user.id,
            AuditLog.action == "demo_ai_request",
            AuditLog.created_at >= cutoff,
        ).count()
        if used >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"The shared public demo is limited to {limit} AI requests per rolling hour. Please try later.",
            )
        db.add(AuditLog(
            actor_user_id=user.id,
            organization_id=user.organization_id,
            action="demo_ai_request",
            details={"quota_per_hour": limit},
        ))
        db.commit()

    # The OpenAI credential is read only by the backend service and is never returned.
    return ask(db, request)
