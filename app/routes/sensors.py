from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.psql import get_db
from app.schemas import SensorCreate
from app import models

router = APIRouter()

@router.post("/sensors/data", status_code=201)
def ingest(reading: SensorCreate, db: Session = Depends(get_db)):
    # 1. Create a SensorEvent model instance from the reading
    sensor_event = models.SensorEvent(
        device_id=reading.device_id,
        temperature=reading.temperature,
        humidity=reading.humidity
    )
    # 2. Add it to the db session
    db.add(sensor_event)
    # 3. Commit
    db.commit()
    db.refresh(sensor_event)
    # 4. Return something
    return {"status": "success", "id": sensor_event.id}
