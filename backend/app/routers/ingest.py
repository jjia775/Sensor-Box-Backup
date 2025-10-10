from typing import Any, List, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, text
from ..models import SensorReading
from ..deps import get_db

router = APIRouter(tags=["ingest"])

# 简单输入模型（也可直接用 dict）
def _coerce_row(row: dict[str, Any]) -> dict[str, Any]:
    try:
        sid = UUID(str(row["sensor_id"]))
        val = float(row["value"])
    except Exception:
        raise HTTPException(status_code=400, detail="bad sensor_id or value")
    attrs = row.get("attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}
    return {"sensor_id": sid, "value": val, "attributes": attrs}

@router.post("/ingest")
async def ingest(payload: Union[dict, List[dict]], db: AsyncSession = Depends(get_db)):
    rows = payload if isinstance(payload, list) else [payload]
    data = [_coerce_row(r) for r in rows]

    # 写入只做一件事：插入。不要在这里 JOIN、查 sensor、做复杂逻辑
    # 可选：降低持久化延迟（掉电可能丢最近几条）——提升吞吐
    await db.execute(text("SET LOCAL synchronous_commit = OFF"))

    stmt = insert(SensorReading).values(data)
    await db.execute(stmt)
    await db.commit()
    return {"ok": True, "n": len(data)}
