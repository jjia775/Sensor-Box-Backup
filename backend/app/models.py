import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, JSON, ForeignKey, DateTime, func
from sqlalchemy import String, Boolean, TIMESTAMP, text, ForeignKey, Float, BigInteger, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    sensors = relationship("Sensor", back_populates="owner")

class Sensor(Base):
    __tablename__ = "sensors"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), index=True)
    type: Mapped[str] = mapped_column(String(80), index=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    owner = relationship("User", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    configs = relationship("SensorConfig", back_populates="sensor", cascade="all, delete-orphan")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sensor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sensors.id", ondelete="CASCADE"), index=True)
    ts: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), index=True)
    value: Mapped[float] = mapped_column(Float)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sensor = relationship("Sensor", back_populates="readings")

Index("ix_readings_sensor_ts_desc", SensorReading.sensor_id, SensorReading.ts.desc())

class SensorConfig(Base):
    __tablename__ = "sensor_configs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sensors.id", ondelete="CASCADE"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    sensor = relationship("Sensor", back_populates="configs")
