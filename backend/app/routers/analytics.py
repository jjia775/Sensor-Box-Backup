from fastapi import APIRouter, Depends
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from ..models import SensorReading, Sensor
from ..deps import get_db

router = APIRouter(prefix="/api/charts", tags=["charts"])

THRESHOLDS = {
    "co": {"unit": "ppm", "lines": [{"label": "WHO 1-h", "kind": "upper", "value": 30.0}]},
    "co2": {"unit": "ppm", "lines": [{"label": "ASHRAE", "kind": "upper", "value": 1000.0}]},
    "light_night": {"unit": "lux", "lines": [{"label": "IES", "kind": "lower", "value": 100.0}, {"label": "IES", "kind": "upper", "value": 200.0}]},
    "no2": {"unit": "ppb", "lines": [{"label": "WHO 24-h", "kind": "upper", "value": 13.0}]},
    "noise_night": {"unit": "dB(A)", "lines": [{"label": "WHO night 8h", "kind": "upper", "value": 30.0}]},
    "o2": {"unit": "% vol", "lines": [{"label": "OSHA", "kind": "lower", "value": 19.5}]},
    "pm25": {"unit": "µg/m³", "lines": [{"label": "WHO 24-h", "kind": "upper", "value": 15.0}]},
    "rh": {"unit": "%", "lines": [{"label": "WHO/ASHRAE", "kind": "lower", "value": 30.0}, {"label": "WHO/ASHRAE", "kind": "upper", "value": 60.0}]},
    "temp": {"unit": "°C", "lines": [{"label": "WHO", "kind": "lower", "value": 18.0}, {"label": "WHO", "kind": "upper", "value": 24.0}]},
}

ALIASES: dict[str, list[str]] = {
    "temp": ["temp", "temperature"],
    "rh": ["rh", "humidity"],
    "pm25": ["pm25", "pm2_5", "pm2.5"],
    "co2": ["co2"],
    "co": ["co"],
    "no2": ["no2"],
    "o2": ["o2"],
    "light_night": ["light_night", "light"],
    "noise_night": ["noise_night", "noise"],
}

def _parse_interval(s: str) -> timedelta:
    u = s[-1].lower()
    v = int(s[:-1])
    if u == "s": return timedelta(seconds=v)
    if u == "m": return timedelta(minutes=v)
    if u == "h": return timedelta(hours=v)
    if u == "d": return timedelta(days=v)
    raise ValueError("bad interval")

def _bucket(ts: datetime, start: datetime, step: timedelta) -> datetime:
    n = int((ts - start).total_seconds() // step.total_seconds())
    return start + n * step

@router.get("/metrics")
def list_metrics():
    out = []
    for k, cfg in THRESHOLDS.items():
        out.append({"metric": k, "unit": cfg["unit"], "thresholds": cfg["lines"]})
    return {"metrics": out}

@router.post("/metric_timeseries")
async def metric_timeseries(payload: dict, db: AsyncSession = Depends(get_db)):
    serial = (
        payload.get("serial_number")
        or payload.get("serial")
        or payload.get("sensor_serial")
        or payload.get("serial_id")
        or payload.get("sensor_box_id")  # 兼容旧前端，若还在传 box 字段，这里当作 serial 用
    )
    if not serial:
        return {"title": "Missing serial_number", "unit": "", "labels": [], "series": [{"name": "n/a", "data": []}], "thresholds": []}

    metric = str(payload["metric"]).lower()
    start_ts = datetime.fromisoformat(payload["start_ts"])
    end_ts = datetime.fromisoformat(payload["end_ts"])
    interval = _parse_interval(payload.get("interval", "5m"))
    agg = payload.get("agg", "avg")
    title = payload.get("title") or f"{metric.upper()} vs Time"

    types = [t.lower() for t in ALIASES.get(metric, [metric])]

    stmt = (
        select(SensorReading.ts, SensorReading.value)
        .join(Sensor, Sensor.id == SensorReading.sensor_id)
        .where(
            func.lower(Sensor.type).in_(types),
            SensorReading.ts >= start_ts,
            SensorReading.ts <= end_ts,
            or_(
                Sensor.serial_number == serial,
                SensorReading.attributes.op("->>")("serial_number") == serial,
            ),
        )
        .order_by(SensorReading.ts.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    cfg = THRESHOLDS.get(metric, {"unit": "", "lines": []})
    if not rows:
        return {"title": title, "unit": cfg["unit"], "labels": [], "series": [{"name": metric, "data": []}], "thresholds": cfg["lines"]}

    base = rows[0][0].replace(second=0, microsecond=0)
    buckets: dict[datetime, list[float]] = {}
    for ts, val in rows:
        b = _bucket(ts, base, interval)
        buckets.setdefault(b, []).append(val)

    labels, data = [], []
    for k in sorted(buckets.keys()):
        vals = buckets[k]
        if agg == "min": v = min(vals)
        elif agg == "max": v = max(vals)
        elif agg == "last": v = vals[-1]
        elif agg == "sum": v = sum(vals)
        else: v = sum(vals) / len(vals)
        labels.append(k.isoformat())
        data.append(v)

    return {"title": title, "unit": cfg["unit"], "labels": labels, "series": [{"name": metric, "data": data}], "thresholds": cfg["lines"]}
