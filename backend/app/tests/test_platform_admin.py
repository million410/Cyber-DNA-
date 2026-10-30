from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.endpoints import platform
from app.db.database import Base, get_db
from app.db.models import Organization, AuthUser, AuthSession, Event, OnboardingState
from app.services.security import get_principal


def make_app(role="platform_admin"):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with TestingSession() as db:
        org_a = Organization(name="Tenant A", status="active")
        org_b = Organization(name="Tenant B", status="onboarding")
        db.add_all([org_a, org_b])
        db.flush()
        admin = AuthUser(username="platform-root", password_hash="unused", role=role,
                         organization_id=org_a.id, is_active=True, must_change_password=False)
        tenant_user = AuthUser(username="tenant-user", password_hash="unused", role="org_admin",
                               organization_id=org_b.id, is_active=True, must_change_password=False)
        db.add_all([admin, tenant_user])
        db.flush()
        db.add_all([
            OnboardingState(organization_id=org_a.id),
            OnboardingState(organization_id=org_b.id),
            Event(organization_id=org_a.id, timestamp=datetime.now(timezone.utc), event_id=4624),
            Event(organization_id=org_b.id, timestamp=datetime.now(timezone.utc), event_id=4625),
        ])
        db.commit()
        admin_id, org_a_id, org_b_id, tenant_user_id = admin.id, org_a.id, org_b.id, tenant_user.id

    app = FastAPI()
    app.include_router(platform.router, prefix="/api/v1")

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    def current_user():
        with TestingSession() as db:
            return db.query(AuthUser).filter(AuthUser.id == admin_id).one()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_principal] = current_user
    return app, engine, TestingSession, org_a_id, org_b_id, tenant_user_id


def test_platform_admin_can_list_all_tenants_and_usage():
    app, engine, _, org_a, org_b, _ = make_app()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/platform/organizations")
            assert response.status_code == 200
            body = response.json()
            assert body["total"] == 2
            assert {item["id"] for item in body["items"]} == {org_a, org_b}
            assert sum(item["events"] for item in body["items"]) == 2
            overview = client.get("/api/v1/platform/overview")
            assert overview.status_code == 200
            assert overview.json()["organizations"] == 2
            assert overview.json()["events"] == 2
    finally:
        engine.dispose()


def test_disabling_platform_user_revokes_existing_sessions():
    app, engine, TestingSession, _, _, target_id = make_app()
    try:
        with TestingSession() as db:
            db.add(AuthSession(token_hash="test-session-hash", user_id=target_id,
                               expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
            db.commit()
        with TestClient(app) as client:
            response = client.patch(f"/api/v1/platform/users/{target_id}/access", json={"is_active": False})
            assert response.status_code == 200
            assert response.json()["is_active"] is False
            assert response.json()["sessions_revoked"] is True
        with TestingSession() as db:
            session = db.query(AuthSession).filter_by(user_id=target_id).one()
            assert session.revoked_at is not None
            user = db.query(AuthUser).filter_by(id=target_id).one()
            assert user.is_active is False
    finally:
        engine.dispose()


def test_non_platform_user_is_denied_from_platform_routes():
    app, engine, _, _, _, _ = make_app(role="org_admin")
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/platform/organizations")
            assert response.status_code == 403
    finally:
        engine.dispose()
