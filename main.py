from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import CalendarEvent, ChecklistTask
from schemas import CalendarEventOut, ChecklistTaskOut

app = FastAPI()

# Allow the React dev server (localhost:5173) to call this API.
# Without this, the browser blocks the request as a security measure (CORS).
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