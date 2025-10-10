from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas import RegisterIn, RegisterOut
from app.models import Household
from app.utils import build_house_id
from app.db import get_db

router = APIRouter(prefix="/api", tags=["registration"])

@router.post("/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    house_id = build_house_id(data.zone, data.householder, data.serial_number)
    q1 = select(Household).where(Household.serial_number == data.serial_number)
    q2 = select(Household).where(Household.house_id == house_id)
    if (await db.execute(q1)).scalars().first():
        raise HTTPException(status_code=409, detail="Serial number already exists")
    if (await db.execute(q2)).scalars().first():
        raise HTTPException(status_code=409, detail="House ID conflict")
    obj = Household(
        serial_number=data.serial_number,
        householder=data.householder,
        phone=data.phone,
        email=data.email,
        address=data.address,
        zone=data.zone,
        house_id=house_id,
    )
    db.add(obj)
    print("INSERT", house_id)
    await db.commit()
    return RegisterOut(house_id=house_id)
