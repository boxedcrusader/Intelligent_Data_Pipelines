from pydantic import BaseModel
from datetime import datetime

class SensorCreate(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    