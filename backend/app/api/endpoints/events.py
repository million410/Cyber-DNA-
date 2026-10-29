from collections import Counter
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.schemas import EventResponse, EventStats
from app.db.database import get_db
from app.db.models import Event, Computer

router = APIRouter()

@router.get("/events", response_model=List[EventResponse])
def get_events(
    page: int = 1,
    limit: int = 50,
    event_id: Optional[int] = None,
    username: Optional[str] = None,
    computer: Optional[str] = None,
    result: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if computer:
        query = query.join(Computer).filter(Computer.hostname == computer)
    if event_id is not None:
        query = query.filter(Event.event_id == event_id)
    if username:
        query = query.filter(Event.username == username)
    if result:
        query = query.filter(Event.result == result)
    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)

    offset = (page - 1) * limit
    events = query.order_by(Event.timestamp.desc()).offset(offset).limit(limit).all()
    return events

@router.get("/events/stats", response_model=EventStats)
def get_events_stats(db: Session = Depends(get_db)):
    """Return tenant-scoped event totals and useful breakdowns."""
    total = db.query(Event).count()

    event_rows = (
        db.query(Event.event_id, func.count(Event.id))
        .group_by(Event.event_id)
        .all()
    )
    by_event_id = {
        str(event_id if event_id is not None else "unknown"): count
        for event_id, count in event_rows
    }

    result_rows = (
        db.query(Event.result, func.count(Event.id))
        .group_by(Event.result)
        .all()
    )
    by_result = {
        str(result if result is not None and str(result).strip() else "unknown"): count
        for result, count in result_rows
    }

    # Build a stable, zero-filled 24-hour series in UTC. Grouping in Python
    # keeps this compatible with both PostgreSQL production and SQLite tests.
    now = datetime.now(timezone.utc)
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    window_start = current_hour - timedelta(hours=23)
    hourly_counts = Counter()
    recent_timestamps = (
        db.query(Event.timestamp)
        .filter(Event.timestamp >= window_start, Event.timestamp <= now)
        .all()
    )
    for (timestamp,) in recent_timestamps:
        if timestamp is None:
            continue
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        hourly_counts[hour] += 1

    by_hour = [
        {"hour": (window_start + timedelta(hours=offset)).isoformat(), "count": hourly_counts[window_start + timedelta(hours=offset)]}
        for offset in range(24)
    ]

    return EventStats(
        total=total,
        by_event_id=by_event_id,
        by_result=by_result,
        by_hour=by_hour,
    )

@router.get("/events/{event_id_param}", response_model=EventResponse)
def get_event(event_id_param: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id_param).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
