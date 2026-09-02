from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date as date_type, datetime
import shutil
import json
import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from database import get_db
from models import CalendarEvent, ChecklistTask, Subsystem, Consumable, FixedLifeSpare, TaskAuditLog, PMRecord, UploadLog, RescheduleLog
from schemas import (
    CalendarEventOut,
    ChecklistTaskOut,
    SummaryOut,
    ConsumableOut,
    SpareOut,
    ChecklistTaskUpdate,
    TaskAuditLogOut,
    UploadResultOut,
    LastUpdateOut,
    EligibilityOut,
    RescheduleRequest,
    RescheduleResultOut
)
from ingest import run_full_ingestion

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
    eligible_subsystem_ids = set(e.subsystem_id for e in events_today)
    subsystems_eligible = len(eligible_subsystem_ids)

    # MET-001: count checklist tasks belonging to today's eligible subsystems
    planned_checks_today = 0
    if eligible_subsystem_ids:
        planned_checks_today = (
            db.query(func.count(ChecklistTask.id))
            .filter(ChecklistTask.subsystem_id.in_(eligible_subsystem_ids))
            .scalar() or 0
        )

    # MET-002: sum SUBSYSTEM_MASTER.Est_Duration_hrs for eligible subsystems (per spec, not per calendar row)
    estimated_maintenance_hours = 0.0
    if eligible_subsystem_ids:
        estimated_maintenance_hours = (
            db.query(func.sum(Subsystem.est_duration_hrs))
            .filter(Subsystem.subsystem_id.in_(eligible_subsystem_ids))
            .scalar() or 0.0
        )

    # MET-004: % of today's eligible tasks marked COMPLETE
    status_percentage = 0
    if planned_checks_today > 0:
        completed_count = (
            db.query(func.count(ChecklistTask.id))
            .filter(ChecklistTask.subsystem_id.in_(eligible_subsystem_ids))
            .filter(ChecklistTask.completion_status == "COMPLETE")
            .scalar() or 0
        )
        status_percentage = round((completed_count / planned_checks_today) * 100)

    # MET-005: Low Stock Alerts
    low_stock_alerts = (
        db.query(func.count(Consumable.id)).filter(Consumable.status == "Low Stock").scalar() or 0
    )

    # MET-006: Life Span Alerts (expired or within warning window)
    life_span_alerts = (
        db.query(func.count(FixedLifeSpare.id)).filter(FixedLifeSpare.status == "Low Stock").scalar() or 0
    )

    # MET-007: Total Active Subsystems
    total_active_subsystems = (
        db.query(func.count(Subsystem.subsystem_id)).filter(Subsystem.active_flag == "Y").scalar() or 0
    )

    # MET-008: PM Completion Rate (currently all-time, see note below)
    total_pm_records = db.query(func.count(PMRecord.record_id)).scalar() or 0
    completed_pm_records = (
        db.query(func.count(PMRecord.record_id)).filter(PMRecord.overall_status == "COMPLETE").scalar() or 0
    )
    pm_completion_rate_mtd = round((completed_pm_records / total_pm_records) * 100) if total_pm_records > 0 else 0

    return SummaryOut(
        planned_checks_today=planned_checks_today,
        estimated_maintenance_hours=estimated_maintenance_hours,
        subsystems_eligible=subsystems_eligible,
        status_percentage=status_percentage,
        low_stock_alerts=low_stock_alerts,
        life_span_alerts=life_span_alerts,
        total_active_subsystems=total_active_subsystems,
        pm_completion_rate_mtd=pm_completion_rate_mtd,
    )


@app.get("/api/eligibility/{event_date}", response_model=List[EligibilityOut])
def get_eligibility(event_date: date_type, db: Session = Depends(get_db)):
    events_today = db.query(CalendarEvent).filter(CalendarEvent.event_date == event_date).all()
    eligible_ids = list(set(e.subsystem_id for e in events_today))

    if not eligible_ids:
        return []

    subsystems = db.query(Subsystem).filter(Subsystem.subsystem_id.in_(eligible_ids)).all()
    return subsystems


@app.post("/api/reschedule", response_model=RescheduleResultOut)
def reschedule_pm(request: RescheduleRequest, db: Session = Depends(get_db)):
    event = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.subsystem_id == request.subsystem_id, CalendarEvent.event_date == request.original_date)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="No scheduled event found for that subsystem/date")
    
    event.event_date = request.new_date
    count = db.query(func.count(RescheduleLog.log_id)).scalar() or 0
    new_log_id = f"RSC-{count + 1:03d}"
    
    log_entry = RescheduleLog(
        log_id=new_log_id,
        subsystem_id=request.subsystem_id,
        original_date=request.original_date,
        new_date=request.new_date,
        reason_for_rescheduling=request.reason,
        requested_by="current_user",
        status="APPROVED",
        timestamp=datetime.utcnow(),
    )
    db.add(log_entry)
    db.commit()
    
    return RescheduleResultOut(
        log_id=new_log_id, 
        original_date=request.original_date, 
        new_date=request.new_date, 
        status="APPROVED"
    )


@app.get("/api/export/{event_date}")
def export_plan_pdf(event_date: date_type, db: Session = Depends(get_db)):
    events_today = db.query(CalendarEvent).filter(CalendarEvent.event_date == event_date).all()
    eligible_ids = list(set(e.subsystem_id for e in events_today))
    subsystems = db.query(Subsystem).filter(Subsystem.subsystem_id.in_(eligible_ids)).all()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"RPM Dashboard — Maintenance Plan for {event_date}")
    y -= 40
    
    for sub in subsystems:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"{sub.subsystem_full_name} ({sub.pm_frequency}) — {sub.est_duration_hrs}h")
        y -= 20
        tasks = db.query(ChecklistTask).filter(ChecklistTask.subsystem_id == sub.subsystem_id).order_by(ChecklistTask.step_no).all()
        p.setFont("Helvetica", 10)
        for task in tasks:
            p.drawString(70, y, f"{task.step_no}. {task.task_title} ({task.approx_time_min} min)")
            y -= 15
            if y < 50:
                p.showPage()
                y = 750
        y -= 15
        
    p.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=maintenance_plan_{event_date}.pdf"},
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

    old_status = task.completion_status
    task.completion_status = update.completion_status

    log_entry = TaskAuditLog(
        task_id=task_id,
        old_status=old_status,
        new_status=update.completion_status,
        changed_by="current_user",
        changed_at=datetime.utcnow(),
    )
    db.add(log_entry)

    db.commit()
    db.refresh(task)

    return task


@app.get("/api/audit-log/{task_id}", response_model=List[TaskAuditLogOut])
def get_task_audit_log(task_id: str, db: Session = Depends(get_db)):
    logs = (
        db.query(TaskAuditLog)
        .filter(TaskAuditLog.task_id == task_id)
        .order_by(TaskAuditLog.changed_at.desc())
        .all()
    )
    return logs


@app.post("/api/admin/upload-excel", response_model=UploadResultOut)
def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

    save_path = "RPM_Dashboard_InputData_v10.xlsx"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        summary = run_full_ingestion(db)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process Excel file: {str(e)}")

    log_entry = UploadLog(
        filename=file.filename,
        uploaded_at=datetime.utcnow(),
        summary=json.dumps(summary),
    )
    db.add(log_entry)
    db.commit()

    return UploadResultOut(
        filename=file.filename,
        uploaded_at=log_entry.uploaded_at,
        summary=summary,
    )


@app.get("/api/admin/last-update", response_model=LastUpdateOut)
def get_last_update(db: Session = Depends(get_db)):
    latest = db.query(UploadLog).order_by(UploadLog.uploaded_at.desc()).first()
    if not latest:
        return LastUpdateOut(filename=None, uploaded_at=None)
    return LastUpdateOut(filename=latest.filename, uploaded_at=latest.uploaded_at)