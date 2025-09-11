from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import Sensor, SensorReading
from ..deps import get_db

router = APIRouter()

@router.post("/ingest")
def ingest(payload: dict, db: Session = Depends(get_db)):
    sensor = db.get(Sensor, payload["sensor_id"])
    if not sensor:
        raise HTTPException(400, "unknown sensor_id")
    obj = SensorReading(sensor_id=sensor.id, value=float(payload["value"]), attributes=payload.get("attributes"))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id}
