from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_db
from ..models import Sensor

router = APIRouter()

@router.get("/")
async def list_sensors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sensor))
    return result.scalars().all()
