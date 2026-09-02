from pydantic import BaseModel
from datetime import date, datetime
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
    low_stock_alerts: int
    life_span_alerts: int
    total_active_subsystems: int
    pm_completion_rate_mtd: int


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
    replacement_action: Optional[str] = None
    storage_location: Optional[str] = None

    class Config:
        from_attributes = True


class ChecklistTaskUpdate(BaseModel):
    completion_status: str

    class Config:
        from_attributes = True


class TaskAuditLogOut(BaseModel):
    id: int
    task_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


class UploadResultOut(BaseModel):
    filename: str
    uploaded_at: datetime
    summary: dict


class LastUpdateOut(BaseModel):
    filename: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class EligibilityOut(BaseModel):
    subsystem_id: str
    subsystem_full_name: str
    pm_frequency: str
    est_duration_hrs: float

    class Config:
        from_attributes = True


class RescheduleRequest(BaseModel):
    subsystem_id: str
    original_date: date
    new_date: date
    reason: str


class RescheduleResultOut(BaseModel):
    log_id: str
    original_date: date
    new_date: date
    status: str

    class Config:
        from_attributes = True