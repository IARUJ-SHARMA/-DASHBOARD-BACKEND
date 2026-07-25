from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Subsystem(Base):
    __tablename__ = "subsystems"

    subsystem_id = Column(String, primary_key=True)  # e.g. 'LCU', 'Rectifier'
    subsystem_full_name = Column(String)
    pm_frequency = Column(String)            # Weekly / Monthly / Quarterly / Annual
    freq_colour_code = Column(String)      # 'Blue', 'Red', etc.
    hex_colour = Column(String)              # '#1D4ED8'
    est_duration_hrs = Column(Float)
    display_order = Column(Integer)
    active_flag = Column(String)
    dashboard_icon = Column(String)
    subsystem_category = Column(String)
    syrs_ref = Column(String)
    notes = Column(Text)
    last_updated = Column(Date)

    tasks = relationship("ChecklistTask", back_populates="subsystem")
    spares = relationship("FixedLifeSpare", back_populates="subsystem")
    calendar_events = relationship("CalendarEvent", back_populates="subsystem")


class ChecklistTask(Base):
    __tablename__ = "checklist_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subsystem_id = Column(String, ForeignKey("subsystems.subsystem_id"))
    task_id = Column(String, unique=True)   # e.g. 'LCU-T01'
    step_no = Column(Integer)
    checklist_item_short = Column(String)
    task_title = Column(String)
    task_description = Column(Text)
    approx_time_min = Column(Integer)
    special_tools = Column(String)
    ppe_requirements = Column(String)
    video_ref_filename = Column(String)
    image_ref_filename = Column(String)
    mandatory_flag = Column(String)
    syrs_ref = Column(String)
    completion_status = Column(String, default="PENDING")
    notes = Column(Text)

    subsystem = relationship("Subsystem", back_populates="tasks")


class Consumable(Base):
    __tablename__ = "consumables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, unique=True)   # e.g. 'C-001'
    consumable_item_name = Column(String)
    associated_subsystems = Column(String)
    unit_of_measure = Column(String)
    current_qty = Column(Float)
    alert_threshold = Column(Float)
    status = Column(String)                 # 'Adequate', 'Low Stock', etc.
    last_replenished = Column(Date)
    supplier_ref = Column(String)
    storage_location = Column(String)
    syrs_ref = Column(String)
    notes = Column(Text)


class FixedLifeSpare(Base):
    __tablename__ = "fixed_life_spares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spare_id = Column(String, unique=True)  # e.g. 'S-001'
    spare_item_name = Column(String)
    subsystem_id = Column(String, ForeignKey("subsystems.subsystem_id"))
    total_life_months = Column(Integer)
    install_date = Column(Date)
    replace_by_date = Column(Date)
    months_remaining = Column(Integer)
    status = Column(String)
    alert_level = Column(String)
    supplier_part_no = Column(String)
    storage_location = Column(String)
    syrs_ref = Column(String)
    replacement_action = Column(Text)

    subsystem = relationship("Subsystem", back_populates="spares")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(Date)
    day_of_week = Column(String)
    subsystem_id = Column(String, ForeignKey("subsystems.subsystem_id"))
    subsystem_name = Column(String)
    pm_frequency = Column(String)
    colour_code = Column(String)
    duration_hrs = Column(Float)
    calendar_label = Column(String)
    notes = Column(Text)

    subsystem = relationship("Subsystem", back_populates="calendar_events")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True)   # e.g. 'ADMIN001'
    full_name = Column(String)
    role = Column(String)                   # Administrator / Engineer / Technician
    permissions = Column(Text)
    email = Column(String)
    status = Column(String)
    last_login = Column(Date)
    expiry_date = Column(Date)
    notes = Column(Text)


class PMRecord(Base):
    __tablename__ = "pm_records"

    record_id = Column(String, primary_key=True)  # e.g. 'RPM-20260516-001'
    pm_date = Column(Date)
    subsystem_id = Column(String, ForeignKey("subsystems.subsystem_id"))
    technician_id = Column(String)
    tasks_total = Column(Integer)
    tasks_done = Column(Integer)
    completion_pct = Column(String)
    duration_hrs = Column(Float)
    overall_status = Column(String)
    supervisor_id = Column(String)
    rescheduled = Column(String)
    remarks = Column(Text)
    audit_timestamp = Column(DateTime)
    syrs_ref = Column(String)


class RescheduleLog(Base):
    __tablename__ = "reschedule_log"

    log_id = Column(String, primary_key=True)   # e.g. 'RSC-001'
    subsystem_id = Column(String, ForeignKey("subsystems.subsystem_id"))
    original_date = Column(Date)
    new_date = Column(Date)
    reason_for_rescheduling = Column(Text)
    authorised_by = Column(String)
    requested_by = Column(String)
    status = Column(String)
    timestamp = Column(DateTime)
    notes = Column(Text)


class TaskAuditLog(Base):
    __tablename__ = "task_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("checklist_tasks.task_id"))
    old_status = Column(String)
    new_status = Column(String)
    changed_by = Column(String)
    changed_at = Column(DateTime)