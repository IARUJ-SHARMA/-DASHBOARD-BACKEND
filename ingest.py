import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import (
    Subsystem, ChecklistTask, Consumable,
    FixedLifeSpare, CalendarEvent, User, PMRecord, RescheduleLog)

EXCEL_FILE = "RPM_Dashboard_InputData_v10.xlsx"

def load_sheet(sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, skiprows=3)
    return df

def clean_rows(df: pd.DataFrame, id_column: str) -> pd.DataFrame:
    df = df.dropna(subset=[id_column])
    return df

def ingest_subsystems(db: Session):
    df = load_sheet("SUBSYSTEM_MASTER")
    df = clean_rows(df, "Subsystem_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.get(Subsystem, row["Subsystem_ID"])
        values = dict(
            subsystem_full_name=row["Subsystem_Full_Name"],
            pm_frequency=row["PM_Frequency"],
            freq_colour_code=row["Freq_Colour_Code"],
            hex_colour=row["Hex_Colour"],
            est_duration_hrs=row["Est_Duration_hrs"],
            display_order=row["Display_Order"],
            active_flag=row["Active_Flag"],
            dashboard_icon=row["Dashboard_Icon"],
            subsystem_category=row["Subsystem_Category"],
            syrs_ref=row["SyRS_Ref"],
            notes=row["Notes"],
            last_updated=row["Last_Updated"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(Subsystem(subsystem_id=row["Subsystem_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_checklist_tasks(db: Session):
    df = load_sheet("CHECKLIST_TASKS")
    df = clean_rows(df, "Task_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.query(ChecklistTask).filter_by(task_id=row["Task_ID"]).first()
        values = dict(
            subsystem_id=row["Subsystem_ID"],
            step_no=row["Step_No"],
            checklist_item_short=row["Checklist_Item_Short"],
            task_title=row["Task_Title"],
            task_description=row["Task_Description"],
            approx_time_min=row["Approx_Time_min"],
            special_tools=row["Special_Tools"],
            ppe_requirements=row["PPE_Requirements"],
            video_ref_filename=row["Video_Ref_Filename"],
            image_ref_filename=row["Image_Ref_Filename"],
            mandatory_flag=row["Mandatory_Flag"],
            syrs_ref=row["SyRS_Ref"],
            notes=row["Notes"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(ChecklistTask(task_id=row["Task_ID"], completion_status="PENDING", **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_consumables(db: Session):
    df = load_sheet("CONSUMABLES")
    df = clean_rows(df, "Item_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.query(Consumable).filter_by(item_id=row["Item_ID"]).first()
        values = dict(
            consumable_item_name=row["Consumable_Item_Name"],
            associated_subsystems=row["Associated_Subsystems"],
            unit_of_measure=row["Unit_of_Measure"],
            current_qty=row["Current_Qty"],
            alert_threshold=row["Alert_Threshold"],
            status=row["Status"],
            last_replenished=row["Last_Replenished"],
            supplier_ref=row["Supplier_Ref"],
            storage_location=row["Storage_Location"],
            syrs_ref=row["SyRS_Ref"],
            notes=row["Notes"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(Consumable(item_id=row["Item_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_fixed_life_spares(db: Session):
    df = load_sheet("FIXED_LIFE_SPARES")
    df = clean_rows(df, "Spare_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.query(FixedLifeSpare).filter_by(spare_id=row["Spare_ID"]).first()
        values = dict(
            spare_item_name=row["Spare_Item_Name"],
            subsystem_id=row["Subsystem_ID"],
            total_life_months=row["Total_Life_Months"],
            install_date=row["Install_Date"],
            replace_by_date=row["Replace_By_Date"],
            months_remaining=row["Months_Remaining"],
            status=row["Status"],
            alert_level=row["Alert_Level"],
            supplier_part_no=row["Supplier_Part_No"],
            storage_location=row["Storage_Location"],
            syrs_ref=row["SyRS_Ref"],
            replacement_action=row["Replacement_Action"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(FixedLifeSpare(spare_id=row["Spare_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_calendar_events(db: Session):
    df = load_sheet("CALENDAR_EVENTS")
    df = clean_rows(df, "Subsystem_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = (
            db.query(CalendarEvent)
            .filter_by(event_date=row["Event_Date"], subsystem_id=row["Subsystem_ID"])
            .first()
        )
        values = dict(
            day_of_week=row["Day_of_Week"],
            subsystem_name=row["Subsystem_Name"],
            pm_frequency=row["PM_Frequency"],
            colour_code=row["Colour_Code"],
            duration_hrs=row["Duration_hrs"],
            calendar_label=row["Calendar_Label"],
            notes=row["Notes"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(CalendarEvent(event_date=row["Event_Date"], subsystem_id=row["Subsystem_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_users(db: Session):
    df = load_sheet("USERS_RBAC")
    df = clean_rows(df, "User_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.query(User).filter_by(user_id=row["User_ID"]).first()
        values = dict(
            full_name=row["Full_Name"],
            role=row["Role"],
            permissions=row["Permissions"],
            email=row["Email"],
            status=row["Status"],
            last_login=row["Last_Login"],
            expiry_date=row["Expiry_Date"],
            notes=row["Notes"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(User(user_id=row["User_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_pm_records(db: Session):
    df = load_sheet("PM_RECORDS")
    df = clean_rows(df, "Record_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.get(PMRecord, row["Record_ID"])
        values = dict(
            pm_date=row["PM_Date"],
            subsystem_id=row["Subsystem_ID"],
            technician_id=row["Technician_ID"],
            tasks_total=row["Tasks_Total"],
            tasks_done=row["Tasks_Done"],
            completion_pct=row["Completion_%"],
            duration_hrs=row["Duration_hrs"],
            overall_status=row["Overall_Status"],
            supervisor_id=row["Supervisor_ID"],
            rescheduled=row["Rescheduled"],
            remarks=row["Remarks"],
            audit_timestamp=row["Audit_Timestamp"],
            syrs_ref=row["SyRS_Ref"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(PMRecord(record_id=row["Record_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def ingest_reschedule_log(db: Session):
    df = load_sheet("RESCHEDULE_LOG")
    df = clean_rows(df, "Log_ID")
    inserted, updated = 0, 0

    for _, row in df.iterrows():
        existing = db.get(RescheduleLog, row["Log_ID"])
        values = dict(
            subsystem_id=row["Subsystem_ID"],
            original_date=row["Original_Date"],
            new_date=row["New_Date"],
            reason_for_rescheduling=row["Reason_for_Rescheduling"],
            authorised_by=row["Authorised_By"],
            requested_by=row["Requested_By"],
            status=row["Status"],
            timestamp=row["Timestamp"],
            notes=row["Notes"],
        )
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(RescheduleLog(log_id=row["Log_ID"], **values))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated}

def run_full_ingestion(db: Session) -> dict:
    """Runs every ingestion function and returns a combined summary."""
    return {
        "subsystems": ingest_subsystems(db),
        "checklist_tasks": ingest_checklist_tasks(db),
        "consumables": ingest_consumables(db),
        "fixed_life_spares": ingest_fixed_life_spares(db),
        "calendar_events": ingest_calendar_events(db),
        "users": ingest_users(db),
        "pm_records": ingest_pm_records(db),
        "reschedule_log": ingest_reschedule_log(db),
    }

if __name__ == "__main__":
    db = SessionLocal()
    try:
        summary = run_full_ingestion(db)
        for sheet, counts in summary.items():
            print(f"{sheet}: {counts['inserted']} inserted, {counts['updated']} updated")
    finally:
        db.close()