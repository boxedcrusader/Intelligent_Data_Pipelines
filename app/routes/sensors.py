import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models
from app.db.psql import get_db
from app.db.redis import get_redis
from app.schemas import SensorCreate
from app.services.alert_service import process_alerts

router = APIRouter()

@router.post("/sensors/data", status_code=201)
def ingest(reading: SensorCreate, db: Session = Depends(get_db)):
    
    sensor_event = models.SensorEvent(
        device_id=reading.device_id,
        temperature=reading.temperature,
        humidity=reading.humidity
    )
    
    db.add(sensor_event)
    db.commit()
    db.refresh(sensor_event)

    redis = get_redis()
    key = f"sensor:latest:{sensor_event.device_id}"
    payload = json.dumps({
        "device_id": sensor_event.device_id,
        "temperature": sensor_event.temperature,
        "humidity": sensor_event.humidity,
        "recorded_at": sensor_event.recorded_at.isoformat()
    })
    redis.setex(key, 60, payload)
    
    process_alerts(sensor_event.device_id, sensor_event.temperature, sensor_event.humidity, db)

    return {"status": "success", "id": sensor_event.id}

@router.get("/sensors/{device_id}/latest", status_code=200)
def get_latest_reading(device_id:str, db: Session = Depends(get_db)):
    redis = get_redis()
    key = f"sensor:latest:{device_id}"
    cached = redis.get(key)
    
    if cached:
        data = json.loads(cached)
        data["source"] = "cache"
        return data

    latest_event = db.query(models.SensorEvent).filter(models.SensorEvent.device_id == device_id).order_by(models.SensorEvent.recorded_at.desc()).first()
    
    if not latest_event:
        raise HTTPException(status_code=404, detail="No data found for this device")

    payload = {
        "device_id": latest_event.device_id,
        "temperature": latest_event.temperature,
        "humidity": latest_event.humidity,
        "recorded_at": latest_event.recorded_at.isoformat()
    }
    
    redis.setex(key, 60, json.dumps(payload))
        
    payload["source"] = "database"
    return payload
    
@router.get("/sensors/{device_id}/history", status_code=200)
def get_history(device_id:str, limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(models.SensorEvent).filter(models.SensorEvent.device_id == device_id).order_by(models.SensorEvent.recorded_at.desc()).limit(limit).all()
    
    if not events:
        raise HTTPException(status_code=404, detail="No data found for this device")

    return [
        {
            "device_id": event.device_id,
            "temperature": event.temperature,
            "humidity": event.humidity,
            "recorded_at": event.recorded_at.isoformat()
        }
        for event in events
    ]
