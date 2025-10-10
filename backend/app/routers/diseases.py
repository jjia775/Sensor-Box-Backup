# app/routers/diseases.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/diseases", tags=["diseases"])

# 你可以按需调整：key、显示名、关联的 metric key
# metric 的 key 要和 /api/charts/metrics 里的 metric 保持一致（例如 temp、co2、pm25、rh、no2、co、o2、light_night、noise_night）
DISEASES = [
    {
        "key": "disease1",
        "name": "D1",
        "metrics": ["temp", "co2"],  # 例：疾病1 关联温度、CO2
    },
    {
        "key": "asthma",
        "name": "D2",
        "metrics": ["pm25", "no2", "co2", "rh"],
    },
    {
        "key": "sleep",
        "name": "睡眠障碍",
        "metrics": ["noise_night", "light_night", "temp", "rh"],
    },
]

@router.get("/", summary="列出所有疾病与其关联的 metrics")
def list_diseases():
    return {"diseases": DISEASES}

@router.get("/{key}", summary="获取单个疾病定义")
def get_disease(key: str):
    for d in DISEASES:
        if d["key"] == key:
            return d
    raise HTTPException(status_code=404, detail="Disease not found")
