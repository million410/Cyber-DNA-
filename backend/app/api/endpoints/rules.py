from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas import RuleResponse
from app.db.database import get_db
from app.db.models import DetectionRule

router = APIRouter()

def _canonical_rules(rules: List[DetectionRule], tenant_id: Optional[int]) -> List[DetectionRule]:
    """Hide duplicate legacy rule rows while preserving the existing response shape.

    Older deployments seeded IDs such as org2_RULE-FAILED-LOGON-BURST.
    Newer deployments use ORG-2-RULE-FAILED-LOGON-BURST. Group only rules
    with the same semantic definition and prefer the current tenant namespace.
    The database rows are left untouched so existing alert foreign keys remain safe.
    """
    selected = {}
    for rule in rules:
        key = (
            (rule.name or "").strip().casefold(),
            (rule.type or "").strip().casefold(),
            (rule.logic or "").strip().casefold(),
            (rule.severity or "").strip().casefold(),
        )
        rule_id = str(rule.id)
        if tenant_id is not None and rule_id.startswith(f"ORG-{tenant_id}-"):
            priority = 0
        elif rule_id.startswith("RULE-"):
            priority = 1
        elif tenant_id is not None and rule_id.casefold().startswith(f"org{tenant_id}_".casefold()):
            priority = 2
        else:
            priority = 3
        existing = selected.get(key)
        if existing is None or priority < existing[0]:
            selected[key] = (priority, rule)
    return sorted((entry[1] for entry in selected.values()), key=lambda rule: (rule.name or "").casefold())

@router.get("/rules", response_model=List[RuleResponse])
def get_rules(db: Session = Depends(get_db)):
    rules = db.query(DetectionRule).all()
    return _canonical_rules(rules, db.info.get("organization_id"))

@router.get("/rules/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="DetectionRule not found")
    return rule

@router.get("/rules/{rule_id}/stats")
def get_rule_stats(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="DetectionRule not found")
    return {"alert_count": rule.alert_count}
