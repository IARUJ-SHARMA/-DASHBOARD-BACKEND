from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date as date_type

from database import get_db
from models import CalendarEvent, ChecklistTask, Subsystem, Consumable, FixedLifeSpare
from schemas import (
    CalendarEventOut,
    ChecklistTaskOut,
    SummaryOut,
    ConsumableOut,
    SpareOut,
    ChecklistTaskUpdate,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "RPM Dashboard backend is running"}


@app.get("/api/calendar-events", response_model=List[CalendarEventOut])
def get_calendar_events(db: Session = Depends(get_db)):
    events = db.query(CalendarEvent).all()
    return events


@app.get("/api/checklist/{subsystem_id}", response_model=List[ChecklistTaskOut])
def get_checklist(subsystem_id: str, db: Session = Depends(get_db)):
    tasks = (
        db.query(ChecklistTask)
        .filter(ChecklistTask.subsystem_id == subsystem_id)
        .order_by(ChecklistTask.step_no)
        .all()
    )
    if not tasks:
        raise HTTPException(status_code=404, detail="No checklist tasks found for this subsystem")
    return tasks


@app.get("/api/summary/{event_date}", response_model=SummaryOut)
def get_summary(event_date: date_type, db: Session = Depends(get_db)):
    events_today = db.query(CalendarEvent).filter(CalendarEvent.event_date == event_date).all()

    planned_checks_today = len(events_today)
    estimated_maintenance_hours = sum(e.duration_hrs for e in events_today)
    subsystems_eligible = len(set(e.subsystem_id for e in events_today))

    total_subsystems = db.query(func.count(Subsystem.subsystem_id)).scalar() or 1
    status_percentage = round((subsystems_eligible / total_subsystems) * 100)

    return SummaryOut(
        planned_checks_today=planned_checks_today,
        estimated_maintenance_hours=estimated_maintenance_hours,
        subsystems_eligible=subsystems_eligible,
        status_percentage=status_percentage,
    )


@app.get("/api/consumables", response_model=List[ConsumableOut])
def get_consumables(db: Session = Depends(get_db)):
    items = db.query(Consumable).order_by(Consumable.consumable_item_name).all()
    return items


@app.get("/api/spares", response_model=List[SpareOut])
def get_spares(db: Session = Depends(get_db)):
    items = db.query(FixedLifeSpare).order_by(FixedLifeSpare.months_remaining).all()
    return items


@app.put("/api/checklist/{task_id}/status", response_model=ChecklistTaskOut)
def update_task_status(task_id: str, update: ChecklistTaskUpdate, db: Session = Depends(get_db)):
    task = db.query(ChecklistTask).filter(ChecklistTask.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    valid_statuses = {"PENDING", "IN_PROGRESS", "COMPLETE"}
    if update.completion_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    task.completion_status = update.completion_status
    db.commit()
    db.refresh(task)

    return task