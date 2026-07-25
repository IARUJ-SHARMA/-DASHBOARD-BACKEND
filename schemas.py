from pydantic import BaseModel
from datetime import date
from typing import Optional


class CalendarEventOut(BaseModel):
    id: int
    event_date: date
    day_of_week: str
    subsystem_id: str
    subsystem_name: str
    pm_frequency: str
    colour_code: str
    duration_hrs: float
    calendar_label: Optional[str] = None

    class Config:
        from_attributes = True


class ChecklistTaskOut(BaseModel):
    task_id: str
    step_no: Optional[int] = None
    task_title: str
    task_description: Optional[str] = None
    approx_time_min: Optional[int] = None
    special_tools: Optional[str] = None
    ppe_requirements: Optional[str] = None
    video_ref_filename: Optional[str] = None
    image_ref_filename: Optional[str] = None
    mandatory_flag: Optional[str] = None

    class Config:
        from_attributes = True