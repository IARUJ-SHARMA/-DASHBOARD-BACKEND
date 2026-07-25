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
    completion_status: Optional[str] = None

    class Config:
        from_attributes = True


class SummaryOut(BaseModel):
    planned_checks_today: int
    estimated_maintenance_hours: float
    subsystems_eligible: int
    status_percentage: int


class ConsumableOut(BaseModel):
    item_id: str
    consumable_item_name: str
    associated_subsystems: Optional[str] = None
    unit_of_measure: Optional[str] = None
    current_qty: Optional[float] = None
    alert_threshold: Optional[float] = None
    status: str
    storage_location: Optional[str] = None

    class Config:
        from_attributes = True


class SpareOut(BaseModel):
    spare_id: str
    spare_item_name: str
    subsystem_id: Optional[str] = None
    months_remaining: Optional[int] = None
    status: str
    alert_level: Optional[str] = None
    storage_location: Optional[str] = None

    class Config:
        from_attributes = True


class ChecklistTaskUpdate(BaseModel):
    completion_status: str

    class Config:
        from_attributes = True