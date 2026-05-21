from fastapi import FastAPI
from app import models
from app.routes import sensors
from app.db.psql import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(sensors.router)

@app.get("/server-health")
def server_health():
    return {"status": "ok"}
