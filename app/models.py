from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.psql import Base
from datetime import datetime, timezone

current_time=lambda: datetime.now(timezone.utc)

class SensorEvent(Base):
    __tablename__ = "sensor_events"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String)
    temperature = Column(Float)
    humidity = Column(Float)
    recorded_at = Column(DateTime(timezone=True), default=current_time)
    
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String)
    alert_code = Column(String)
    status = Column(String, nullable=False)
    current_value = Column(Float)
    resolved_at = Column(DateTime(timezone=True), default=None)
    triggered_at = Column(DateTime(timezone=True), default=current_time)
    

