import json
from sqlalchemy.orm import Session
from app.db import redis
from app.db.redis import get_redis
from app import models

TEMP_HIGH = 30.0
TEMP_LOW = 18.0
HUMID_HIGH = 70.0
HUMID_LOW = 40.0

def evaluation_threshold(temperature: float, humidity: float) -> list:
    alerts = []
    if temperature > TEMP_HIGH:
        alerts.append({"code": "TEMP_HIGH", "value": temperature})
    if temperature < TEMP_LOW:
        alerts.append({"code": "TEMP_LOW", "value": temperature})
    if humidity > HUMID_HIGH:
        alerts.append({"code": "HUMID_HIGH", "value": humidity})
    if humidity < HUMID_LOW:
        alerts.append({"code": "HUMID_LOW", "value": humidity})
    return alerts

def process_alerts(device_id: str, temperature: float, humidity: float, db: Session):
    violations = evaluation_threshold(temperature, humidity)
    active_codes = {v["code"] for v in violations}
    
    all_codes = ["TEMP_HIGH", "TEMP_LOW", "HUMID_HIGH", "HUMID_LOW"]

    for code in all_codes:
        redis = get_redis()
        redis_key = f"alert:active:{device_id}:{code}"
        cached_alert = redis.get(redis_key)
        
        if code in active_codes:
            # this code is currently violating the threshold create or update an alert
            if not cached_alert:
                # Create new alert in PostgreSQL
                current_value = next(v["value"] for v in violations if v["code"] == code)
                
                new_alert = models.Alert(
                    device_id=device_id,
                    alert_code=code,
                    status="pending",
                    current_value=current_value
                )
                
                db.add(new_alert)
                db.commit()
                db.refresh(new_alert)
                
                # Cache it in Redis
                redis.set(redis_key, json.dumps({"id": new_alert.id, "alert_code": code}))
                
            else:
                # Update current_value only
                current_value = next(v["value"] for v in violations if v["code"] == code)
                
                alert_data = json.loads(cached_alert)
                
                existing_alert = db.query(models.Alert).filter(models.Alert.id == alert_data["id"]).first()
                existing_alert.current_value = current_value
                db.commit()
                
        else:
            # this code is not violating, resolve if there's an active alert
            if cached_alert:
                alert_data = json.loads(cached_alert)
                existing_alert = db.query(models.Alert).filter(models.Alert.id == alert_data["id"]).first()
                existing_alert.status = "fixed"
                db.commit()
                redis.delete(redis_key)
            
