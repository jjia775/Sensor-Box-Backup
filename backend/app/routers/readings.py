from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from ..models import SensorReading
from ..deps import get_db

router = APIRouter()

@router.post("/api/readings/query")
async def query_readings(payload: dict, db: AsyncSession = Depends(get_db)):
    sensor_id = payload["sensor_id"]
    start_ts = payload.get("start_ts")
    end_ts = payload.get("end_ts")
    limit = int(payload.get("limit", 500))

    stmt = select(SensorReading).where(SensorReading.sensor_id == sensor_id)
    if start_ts:
        stmt = stmt.where(SensorReading.ts >= datetime.fromisoformat(start_ts))
    if end_ts:
        stmt = stmt.where(SensorReading.ts <= datetime.fromisoformat(end_ts))
    stmt = stmt.order_by(desc(SensorReading.ts)).limit(limit)

    res = await db.execute(stmt)
    rows = res.scalars().all()

    return [
        {
            "id": r.id,
            "sensor_id": str(r.sensor_id),
            "ts": r.ts.isoformat(),
            "value": r.value,
            "attributes": r.attributes,
        }
        for r in rows[::-1]
    ]
