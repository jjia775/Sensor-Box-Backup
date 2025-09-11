import uuid
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr

class Config:
    from_attributes = True


class SensorCreate(BaseModel):
    name: str
    type: str
    location: Optional[str] = None
    metadata: Optional[dict] = None


class SensorOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    location: Optional[str] = None
    metadata: Optional[dict] = None


class ConfigCreate(BaseModel):
    value: dict
    is_active: Optional[bool] = True


class ConfigOut(BaseModel):
    id: uuid.UUID
    sensor_id: uuid.UUID
    version: int
    value: dict
    is_active: bool


class ReadingCreate(BaseModel):
    data: dict
    ts: Optional[str] = None
    config_version: Optional[int] = None


class ReadingOut(BaseModel):
    id: uuid.UUID
    sensor_id: uuid.UUID
    ts: Any
    data: dict
    config_version: Optional[int] = None