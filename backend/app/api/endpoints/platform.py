"""Platform-administration read APIs.

Every route is protected by require_platform_admin. Tenant query scoping is
temporarily disabled only after that authorization dependency has succeeded.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    Organization, AuthUser, AuthSession, Event, Alert, Incident,
    CollectorCredential, OnboardingState, AuditLog, PricingRule,
)
from app.services.security import require_platform_admin

router = APIRouter(prefix="/platform", tags=["platform administration"])


def _platform_scope(db: Session) -> None:
    # require_platform_admin is a dependency on every endpoint below.
    # Platform operators need cross-tenant visibility for administration.
    db.info.pop("organization_id", None)


@router.get("/overview")
def platform_overview(
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    organizations = db.query(Organization).count()
    active = db.query(Organization).filter(Organization.status == "active").count()
    users = db.query(AuthUser).filter(AuthUser.role != "demo_viewer").count()
    events = db.query(Event).count()
    alerts = db.query(Alert).count()
    incidents = db.query(Incident).count()
    collectors = db.query(CollectorCredential).filter(CollectorCredential.revoked_at.is_(None)).count()
    return {
        "organizations": organizations,
        "active_organizations": active,
        "users": users,
        "events": events,
        "alerts": alerts,
        "incidents": incidents,
        "active_collector_keys": collectors,
    }


@router.get("/organizations")
def list_organizations(
    status: str | None = Query(default=None, max_length=40),
    search: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    query = db.query(Organization)
    if status:
        query = query.filter(Organization.status == status)
    if search:
        query = query.filter(Organization.name.ilike(f"%{search}%"))
    total = query.count()
    rows = query.order_by(Organization.created_at.desc(), Organization.id.desc()).offset((page - 1) * limit).limit(limit).all()
    items = []
    for org in rows:
        state = db.query(OnboardingState).filter(OnboardingState.organization_id == org.id).first()
        items.append({
            "id": org.id,
            "name": org.name,
            "industry": org.industry,
            "country": org.country,
            "contact_email": org.contact_email,
            "status": org.status,
            "created_at": org.created_at,
            "users": db.query(AuthUser).filter(AuthUser.organization_id == org.id, AuthUser.role != "demo_viewer").count(),
            "events": db.query(Event).filter(Event.organization_id == org.id).count(),
            "alerts": db.query(Alert).filter(Alert.organization_id == org.id).count(),
            "incidents": db.query(Incident).filter(Incident.organization_id == org.id).count(),
            "active_collectors": db.query(CollectorCredential).filter(
                CollectorCredential.organization_id == org.id,
                CollectorCredential.revoked_at.is_(None),
            ).count(),
            "onboarding_completed": bool(state and state.completed),
            "plan_status": state.plan_status if state else "not_selected",
            "activation_status": state.activation_status if state else "not_configured",
        })
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/organizations/{organization_id}")
def organization_detail(
    organization_id: int,
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(404, "Organization not found")
    state = db.query(OnboardingState).filter(OnboardingState.organization_id == org.id).first()
    return {
        "id": org.id, "name": org.name, "industry": org.industry,
        "country": org.country, "timezone": org.timezone,
        "contact_email": org.contact_email, "status": org.status,
        "created_at": org.created_at,
        "onboarding": None if not state else {
            "current_step": state.current_step, "completed": state.completed,
            "assessment": state.assessment or {}, "selected_plan": state.selected_plan,
            "plan_status": state.plan_status, "estimate": state.estimate,
            "activation_status": state.activation_status,
        },
        "usage": {
            "users": db.query(AuthUser).filter(AuthUser.organization_id == org.id, AuthUser.role != "demo_viewer").count(),
            "events": db.query(Event).filter(Event.organization_id == org.id).count(),
            "alerts": db.query(Alert).filter(Alert.organization_id == org.id).count(),
            "incidents": db.query(Incident).filter(Incident.organization_id == org.id).count(),
            "collectors": db.query(CollectorCredential).filter(CollectorCredential.organization_id == org.id, CollectorCredential.revoked_at.is_(None)).count(),
        },
    }


@router.get("/users")
def list_platform_users(
    organization_id: int | None = None,
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    query = db.query(AuthUser).filter(AuthUser.role != "demo_viewer")
    if organization_id is not None:
        query = query.filter(AuthUser.organization_id == organization_id)
    return [{
        "id": user.id, "username": user.username, "email": user.email,
        "role": user.role, "organization_id": user.organization_id,
        "is_active": user.is_active, "must_change_password": user.must_change_password,
        "last_login_at": user.last_login_at, "created_at": user.created_at,
    } for user in query.order_by(AuthUser.created_at.desc()).limit(500).all()]


class UserAccessUpdate(BaseModel):
    is_active: bool


@router.patch("/users/{user_id}/access")
def update_user_access(
    user_id: int,
    body: UserAccessUpdate,
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    target = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == admin.id and not body.is_active:
        raise HTTPException(409, "You cannot disable your own platform administrator account")
    target.is_active = body.is_active
    if not body.is_active:
        db.query(AuthSession).filter(
            AuthSession.user_id == target.id,
            AuthSession.revoked_at.is_(None),
        ).update({AuthSession.revoked_at: datetime.now(timezone.utc)}, synchronize_session=False)
    db.add(AuditLog(
        actor_user_id=admin.id,
        organization_id=target.organization_id,
        action="platform_user_access_changed",
        details={"target_user_id": target.id, "is_active": body.is_active},
    ))
    db.commit()
    return {"user_id": target.id, "is_active": target.is_active, "sessions_revoked": not body.is_active}


@router.get("/audit-logs")
def platform_audit_logs(
    organization_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    query = db.query(AuditLog)
    if organization_id is not None:
        query = query.filter(AuditLog.organization_id == organization_id)
    rows = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).all()
    return [{
        "id": row.id, "actor_user_id": row.actor_user_id,
        "organization_id": row.organization_id, "action": row.action,
        "details": row.details, "created_at": row.created_at,
    } for row in rows]


@router.get("/pricing-rules")
def list_pricing_rules(
    admin: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    _platform_scope(db)
    return [{
        "key": row.key, "value": row.value, "currency": row.currency,
        "active": row.active, "updated_at": row.updated_at,
    } for row in db.query(PricingRule).order_by(PricingRule.key.asc()).all()]
